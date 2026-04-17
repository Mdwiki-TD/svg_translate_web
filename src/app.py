"""
# isort:skip_file
WSGI entry point for SVG Translate.
"""

from __future__ import annotations
import sys
import logging

try:
    from svg_config import _env_file_path  # Triggers environment configuration
    from logger_config import configure_logging
except ImportError:
    from .svg_config import _env_file_path  # noqa: F401 # Triggers environment configuration
    from .logger_config import configure_logging

level = logging.DEBUG if ("debug" in sys.argv or "DEBUG" in sys.argv) else logging.INFO
configure_logging(level)

try:
    from main_app import create_app
except ImportError:
    from .main_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=level)
