"""
Logging configuration with colored output.
"""

import logging
import os
import sys
from logging.handlers import WatchedFileHandler
from pathlib import Path

import colorlog


def prepare_log_file(log_file: str | None, project_logger: logging.Logger) -> Path | None:
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
        project_logger.error(f"Failed to create log directory: {e}")
        log_file_path = None
    return log_file_path


def setup_logging(
    level: str = "WARNING",
    name: str = "svg_translate_web",
    log_file: str | None = None,
    error_log_file: str | None = None,
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

    console_formatter = colorlog.ColoredFormatter(
        # fmt="%(filename)s:%(lineno)s %(funcName)s() - %(log_color)s%(levelname)-s %(reset)s%(message)s",
        fmt="%(asctime)s - %(name)s - %(log_color)s%(levelname)-s %(reset)s%(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(numeric_level)
    project_logger.addHandler(console_handler)

    project_logger.debug(f"Setting up logging for '{name}' with level '{level}'")

    if log_file:
        log_file = prepare_log_file(log_file, project_logger)
        setup_file_handler(project_logger, log_file, numeric_level)

    if error_log_file:
        error_log_file = prepare_log_file(error_log_file, project_logger)
        setup_file_handler(project_logger, error_log_file, logging.WARNING)


def setup_file_handler(project_logger: logging.Logger, log_file: Path, level: int) -> None:
    if not log_file:
        return
    file_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)-8s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler = WatchedFileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    project_logger.addHandler(file_handler)


def configure_logging(level) -> None:
    # Create log directory if needed
    main_dir = os.getenv("MAIN_DIR", "~/data")
    main_dir = Path(os.path.expandvars(main_dir)).expanduser()

    log_dir = Path(main_dir) / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        setup_logging(level=level, name="main_app")
        logging.getLogger("main_app").warning(
            "Falling back to console logging; could not create log directory %s: %s", log_dir, exc
        )
        return

    # Define paths
    all_log_path = log_dir / "app.log"
    error_log_path = log_dir / "errors.log"

    setup_logging(
        level=level,
        name="main_app",
        log_file=all_log_path,
        error_log_file=error_log_path,
    )
