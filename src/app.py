"""
# isort:skip_file
WSGI entry point for SVG Translate.
"""

from __future__ import annotations

import logging
import os
import sys
from svg_config import _env_file_path  # noqa: F401 # Triggers environment configuration

from main_app import create_app  # noqa: E402
from logger_config import Path, setup_logging

DEBUG = "debug" in sys.argv or "DEBUG" in sys.argv

# Create log directory if needed
main_dir = os.getenv("MAIN_DIR", os.path.join(os.path.expanduser("~"), "data"))

log_dir = Path(main_dir) / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

# Define paths
all_log_path = log_dir / "app.log"
error_log_path = log_dir / "errors.log"

setup_logging(
    level=logging.DEBUG if DEBUG else logging.INFO,
    name=Path(__file__).parent.name,
    log_file=all_log_path,
    error_log_file=error_log_path,
)

app = create_app()

if __name__ == "__main__":
    app.run(debug=DEBUG)
