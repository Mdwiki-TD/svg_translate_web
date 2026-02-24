"""
Logging configuration with colored output.
"""

import logging
import sys
from pathlib import Path

import colorlog


def prepare_log_file(log_file, project_logger):
    log_file = Path(log_file).expanduser()
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        project_logger.error(f"Failed to create log directory: {e}")
        log_file = None
    return log_file


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

    formatter = colorlog.ColoredFormatter(
        fmt="%(filename)s:%(lineno)s %(funcName)s() - %(log_color)s%(levelname)-s %(reset)s%(message)s"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)
    project_logger.addHandler(console_handler)

    if log_file:
        log_file = prepare_log_file(log_file, project_logger)

        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)-8s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(numeric_level)
        project_logger.addHandler(file_handler)

    if error_log_file:
        error_log_file = prepare_log_file(error_log_file, project_logger)

        # Separate error log file
        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)-8s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(error_log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.WARNING)
        project_logger.addHandler(file_handler)
