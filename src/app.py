"""
# isort:skip_file
WSGI entry point for SVG Translate.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from svg_config import _env_file_path  # noqa: F401 # Triggers environment configuration

from logger_config import setup_logging

DEBUG = "debug" in sys.argv or "DEBUG" in sys.argv


def configure_logging():
    # Create log directory if needed
    main_dir = os.getenv("MAIN_DIR", os.path.join(os.path.expanduser("~"), "data"))

    log_dir = Path(main_dir) / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        setup_logging(level=logging.DEBUG if DEBUG else logging.INFO, name="main_app")
        logging.getLogger("main_app").warning(
            "Falling back to console logging; could not create log directory %s: %s", log_dir, exc
        )
        return

    # Define paths
    all_log_path = log_dir / "app.log"
    error_log_path = log_dir / "errors.log"

    setup_logging(
        level=logging.DEBUG if DEBUG else logging.INFO,
        name="main_app",
        log_file=all_log_path,
        error_log_file=error_log_path,
    )


configure_logging()

from main_app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run(debug=DEBUG)
