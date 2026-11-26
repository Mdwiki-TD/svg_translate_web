"""Process-level logging for the web workers and the Flask CLI commands.

Call :meth:`ProcessLoggingConfigurator.configure` once from ``app.py``, before
the Flask app is created. Handlers are attached to the *root* logger, so
everything is captured: ``main_app.*``, Flask's ``app.logger``, ``bootstrap``,
``fix_refs``...

    web  -> console (stdout) + app (INFO..WARNING) + errors (ERROR+) log files
    CLI  -> console (stderr) only; the job runner already stores stdout/stderr

Log files: in development a single ``app.log`` / ``errors.log``; in production
one file per UTC day (``app.2024-01-15.log``), see :class:`DailyFileHandler`.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import UTC, datetime
from logging.handlers import WatchedFileHandler
from pathlib import Path
from typing import TextIO

import colorlog

PROJECT_LOGGER_NAME = "main_app"

# format:
_COLOR_FORMAT = (
    "%(asctime)s - %(name)s - %(log_color)s%(levelname)-s %(reset)s- [%(funcName)s:%(lineno)d] - %(message)s"
)

# Standard format: Time - Name - Level - [Func:Line] - Message
_PLAIN_FORMAT = "%(asctime)s - %(name)s - %(levelname)-s - [%(funcName)s:%(lineno)d] - %(message)s"

# format:
_FILE_FORMAT = "%(asctime)s - %(name)s - %(levelname)-8s - %(message)s"


def _to_level(value: str | int, default: int = logging.INFO) -> int:
    """Convert a level name or number to a numeric logging level."""
    if isinstance(value, str):
        return getattr(logging, value.upper(), default)
    return value


class _BelowLevelFilter(logging.Filter):
    """Pass only records whose level is strictly below ``max_level``."""

    def __init__(self, max_level: int) -> None:
        super().__init__()
        self._max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < self._max_level


class DailyFileHandler(logging.FileHandler):
    """Append to ``<stem>.<YYYY-MM-DD>.log``, switching file when the UTC day changes.

    Safe to share between processes (e.g. several uwsgi workers): nothing is ever
    renamed, so there is no rotation race. Each process opens the current day's
    file in append mode and switches to the next one on its own at midnight.
    Only the newest ``backup_count`` files of the same stem are kept.

    Limitations:
    - Relies on POSIX append semantics (production runs on Linux). On Windows,
      O_APPEND is emulated with seek+write and is NOT atomic across processes, so
      concurrent writers can overwrite each other's lines. Fine for a single
      process (dev server); do not run several workers on Windows.
    - A single record larger than the stream buffer (~8 KB, e.g. a huge
      traceback) could in theory interleave with another process's record.
    """

    def __init__(
        self,
        directory: str | Path,
        stem: str,
        *,
        backup_count: int = 90,
        encoding: str = "utf-8",
    ) -> None:
        self._directory = Path(directory)
        self._stem = stem
        self._backup_count = backup_count
        self._day = self._today()
        # delay=True: the file is only opened on the first emitted record
        super().__init__(self._path_for(self._day), mode="a", encoding=encoding, delay=True)
        self._prune()

    @staticmethod
    def _today() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def _path_for(self, day: str) -> str:
        return str(self._directory / f"{self._stem}.{day}.log")

    def _prune(self) -> None:
        """Delete the oldest files so that at most ``backup_count`` remain."""
        if self._backup_count <= 0:
            return
        # ISO dates sort lexicographically, so sorted() is chronological
        files = sorted(self._directory.glob(f"{self._stem}.????-??-??.log"))
        for old in files[: -self._backup_count]:
            try:
                old.unlink()
            except OSError:
                pass  # another process may have deleted it already

    def _switch_day(self, day: str) -> None:
        if self.stream is not None:
            try:
                self.stream.flush()
                self.stream.close()
            finally:
                self.stream = None  # pyright: ignore[reportAttributeAccessIssue] # reopened lazily by FileHandler.emit
        self.baseFilename = os.path.abspath(self._path_for(day))
        self._day = day
        self._prune()

    def emit(self, record: logging.LogRecord) -> None:
        # Handler.handle() already holds the handler lock here
        day = self._today()
        if day != self._day:
            self._switch_day(day)
        super().emit(record)


class ProcessLoggingConfigurator:
    """Configure logging for the whole process (web worker or CLI command).

    Sets up the console handler and, for web processes only, the app and
    errors file handlers.
    """

    _configured: bool = False

    @staticmethod
    def is_cli_process() -> bool:
        """True for ``flask <command>`` runs (run-job, ...), False for web workers.

        ``CLI_MODE=1`` (exported by flask_cmd.sh) is the explicit switch. As a
        fallback, Flask sets ``FLASK_RUN_FROM_CLI`` for every ``flask`` command;
        the dev web server (``flask run``) is excluded.
        """
        if os.environ.get("CLI_MODE") == "1":
            return True
        return os.environ.get("FLASK_RUN_FROM_CLI") == "true" and "run" not in sys.argv[1:]

    @staticmethod
    def get_log_dir() -> Path:
        """Return ``$MAIN_DIR/logs`` (default ``~/data/logs``), creating it if needed.

        Reads the environment directly: logging must start before the app config exists.
        """
        main_dir = Path(os.path.expandvars(os.getenv("MAIN_DIR") or "~/data")).expanduser()
        log_dir = main_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    @staticmethod
    def build_console_handler(level: int, *, use_color: bool, stream: TextIO) -> logging.Handler:
        """Create the console handler (colored when ``use_color`` is true)."""
        if use_color:
            formatter: logging.Formatter = colorlog.ColoredFormatter(
                fmt=_COLOR_FORMAT,
                datefmt="%H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
            )
        else:
            formatter = logging.Formatter(fmt=_PLAIN_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)
        handler.setLevel(level)
        return handler

    @staticmethod
    def build_file_handler(
        path: Path,
        level: int,
        *,
        daily_rotation: bool,
        max_level: int | None = None,
    ) -> logging.Handler:
        """Create a file handler for ``path`` (e.g. ``logs/app.log``).

        With ``daily_rotation`` the handler writes ``logs/app.<date>.log`` instead.
        With ``max_level`` records at or above that level are dropped (upper bound).
        """
        if daily_rotation:
            # Not TimedRotatingFileHandler: it renames app.log at midnight, which is
            # NOT safe across processes. uwsgi runs several workers (processes = 2,
            # lazy-apps = true), each with its own handler on the same file; both
            # try to rename it, so lines get lost or land in the wrong day's file.
            # DailyFileHandler never renames: workers just append to the dated file.
            handler: logging.Handler = DailyFileHandler(
                path.parent,
                path.stem,
                backup_count=90,
            )
        else:
            handler = WatchedFileHandler(path, mode="a", encoding="utf-8")

        handler.setFormatter(logging.Formatter(fmt=_FILE_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))
        handler.setLevel(level)
        if max_level is not None:
            handler.addFilter(_BelowLevelFilter(max_level))
        return handler

    @classmethod
    def configure(
        cls,
        *,
        debug: bool = False,
        production: bool = False,
        cli: bool | None = None,
        file_level: str | int = "INFO",
        error_level: str | int = "ERROR",
        errors_in_app_log: bool = False,
        daily_rotation: bool | None = None,
        set_root_level: bool = True,
        name: str | None = None,
    ) -> None:
        """Attach console (and, for web processes, file) handlers to the root logger.

        Args:
            debug: console shows DEBUG instead of INFO.
            production: no colors, one log file per day.
            cli: force CLI/web mode (None = auto-detect with :meth:`is_cli_process`).
            file_level: level of app.log (web only).
            error_level: level of errors.log (web only).
            errors_in_app_log: when False (default) app.log holds only records below
                ``error_level`` and errors go to errors.log alone; when True app.log
                also keeps them, so it is a complete chronological timeline.

        Safe to call more than once; only the first call has an effect.
        """
        if daily_rotation is None:
            daily_rotation = production

        if cls._configured:
            return
        cls._configured = True

        cli = cls.is_cli_process() if cli is None else cli
        console_level = logging.DEBUG if debug else logging.INFO
        app_file_level = _to_level(file_level)
        errors_file_level = _to_level(error_level, default=logging.ERROR)

        handlers: list[logging.Handler] = [
            cls.build_console_handler(
                console_level,
                use_color=not production,
                stream=sys.stderr if cli else sys.stdout,
            )
        ]

        file_error: OSError | None = None
        if not cli:
            try:
                log_dir = cls.get_log_dir()
                handlers.append(
                    cls.build_file_handler(
                        log_dir / "app.log",
                        app_file_level,
                        daily_rotation=daily_rotation,
                        max_level=None if errors_in_app_log else errors_file_level,
                    )
                )
                handlers.append(
                    cls.build_file_handler(
                        log_dir / "errors.log",
                        errors_file_level,
                        daily_rotation=daily_rotation,
                    )
                )
            except OSError as exc:
                file_error = exc

        root = logging.getLogger()
        if set_root_level:
            root.setLevel(logging.WARNING)  # libraries stay quiet

        for handler in handlers:
            root.addHandler(handler)

        logger_name = name or PROJECT_LOGGER_NAME

        # The project logger lets everything through; each handler filters by its own level
        project_level = console_level if cli else min(console_level, app_file_level, errors_file_level)
        logging.getLogger(logger_name).setLevel(project_level)

        if file_error is not None:
            logging.getLogger(logger_name).warning(
                "Falling back to console logging; could not create log directory: %s",
                file_error,
            )


__all__ = [
    "DailyFileHandler",
    "ProcessLoggingConfigurator",
]
