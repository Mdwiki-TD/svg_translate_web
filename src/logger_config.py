"""
Logging configuration with colored output.
"""

import logging
from logging.handlers import WatchedFileHandler
import sys
from pathlib import Path

import colorlog


def prepare_log_file(log_file: str | None, project_logger: logging.Logger) -> Path | None:
    """Prepare the log file path and create parent directories if needed.

    Parameters
    ----------
    log_file : str | None
        Path to the log file.
    project_logger : logging.Logger
        Logger instance for error reporting.

    Returns
    -------
    Path | None
        The expanded log file path, or None if creation failed.
    """
    if log_file is None:
        return None
    log_file_path = Path(log_file).expanduser()
    try:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        project_logger.error(f"Failed to create log directory: {e}")
        return None
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
        setup_file_handler(project_logger, log_file, logging.WARNING)

    if error_log_file:
        error_log_file = prepare_log_file(error_log_file, project_logger)
        setup_file_handler(project_logger, error_log_file, logging.WARNING)


def setup_file_handler(project_logger: logging.Logger, log_file: Path, level: int) -> None:
    file_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)-8s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler = WatchedFileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(level)
    project_logger.addHandler(file_handler)
