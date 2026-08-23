"""
Logging configuration with colored output.
"""

import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler, WatchedFileHandler
from pathlib import Path

import colorlog


def prepare_log_file(
    log_file: str | None,
    project_logger: logging.Logger,
) -> Path | None:
    """
    Prepare the log file path and create parent directories if needed.
    """
    if not log_file:
        return None
    log_file_path = os.path.expandvars(str(log_file))
    log_file_path = Path(log_file_path).expanduser()

    try:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        project_logger.error("Failed to create log directory: %s", e)
        log_file_path = None
    return log_file_path


def setup_file_handler(
    project_logger: logging.Logger,
    log_file: Path,
    level: int,
    daily_rotation: bool = False,
) -> None:
    if not log_file:
        return
    file_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)-8s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if daily_rotation:
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",
            interval=1,
            backupCount=90,
            encoding="utf-8",
            utc=True,
        )
        file_handler.namer = _daily_log_namer
    else:
        file_handler = WatchedFileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    project_logger.addHandler(file_handler)


def setup_logging(
    level: str | int = "WARNING",
    name: str = "main_app",
    log_file: str | None = None,
    error_log_file: str | None = None,
    use_colorlog: bool = False,
    daily_rotation: bool = False,
) -> None:
    """
    Configure logging for the entire project namespace only.
    """
    project_logger = logging.getLogger(name)

    if project_logger.handlers:
        return

    numeric_level = getattr(logging, level.upper(), logging.INFO) if isinstance(level, str) else level

    project_logger.setLevel(numeric_level)
    project_logger.propagate = False

    if use_colorlog:
        console_formatter = colorlog.ColoredFormatter(
            # Standard format: Time - Name - Level - [File:Line] - Message
            fmt="%(asctime)s - %(name)s - %(log_color)s%(levelname)-s %(reset)s- [%(funcName)s:%(lineno)d] - %(message)s",
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
        console_formatter = logging.Formatter(
            # Standard format: Time - Name - Level - [File:Line] - Message
            fmt="%(asctime)s - %(name)s - %(levelname)-s - [%(funcName)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(numeric_level)
    project_logger.addHandler(console_handler)

    project_logger.debug("Setting up logging for '%s' with level '%s'", name, level)

    if log_file:
        log_file_path = prepare_log_file(log_file, project_logger)
        if log_file_path:
            setup_file_handler(project_logger, log_file_path, numeric_level)

    if error_log_file:
        error_log_file_path = prepare_log_file(error_log_file, project_logger)
        if error_log_file_path:
            setup_file_handler(
                project_logger,
                error_log_file_path,
                logging.WARNING,
                daily_rotation=daily_rotation,
            )


def _daily_log_namer(default_name: str) -> str:
    """Rename rotated log from 'errors.log.2024-01-15' to '2024-01-15.log'."""
    directory = os.path.dirname(default_name)
    basename = os.path.basename(default_name)
    # default format: "errors.log.YYYY-MM-DD"
    parts = basename.rsplit(".", 1)
    if len(parts) == 2:
        date_part = parts[1]
        return os.path.join(directory, f"{date_part}.log")
    return default_name


def get_log_dir() -> Path:
    """
    NOTE: Don't use settings.paths.log_dir here, logger must initialize before the app/config is created.
    """
    # Create log directory if needed
    main_dir = os.getenv("MAIN_DIR", "~/data")
    main_dir = Path(os.path.expandvars(main_dir)).expanduser()

    log_dir = Path(main_dir) / "logs"

    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

    return log_dir


def configure_logging(
    level: str | int,
    use_colorlog: bool = False,
    name: str = "main_app",
    daily_rotation: bool = False,
) -> None:
    # Create log directory if needed
    try:
        log_dir = get_log_dir()
    except OSError as exc:
        setup_logging(level=level, name=name, use_colorlog=use_colorlog)
        logging.getLogger(name).warning("Falling back to console logging; could not create log directory %s", exc)
        return

    # Define paths
    all_log_path = str(log_dir / "app.log")
    error_log_path = str(log_dir / "errors.log")

    setup_logging(
        level=level,
        name=name,
        log_file=all_log_path,
        error_log_file=error_log_path,
        use_colorlog=use_colorlog,
        daily_rotation=daily_rotation,
    )


__all__ = [
    "prepare_log_file",
    "setup_file_handler",
    "setup_logging",
    "get_log_dir",
    "configure_logging",
]
