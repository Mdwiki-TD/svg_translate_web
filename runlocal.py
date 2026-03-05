"""
# isort:skip_file
WSGI entry point for SVG Translate.
"""

from __future__ import annotations
import sys

from src.svg_config import _env_file_path  # noqa: F401 # Triggers environment configuration
from src.logger_config import configure_logging

DEBUG = "debug" in sys.argv or "DEBUG" in sys.argv

configure_logging(DEBUG)

from src.main_app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run(debug=DEBUG)
