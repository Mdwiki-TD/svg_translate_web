"""
# isort:skip_file
WSGI production entry point for the app.
"""

from __future__ import annotations
import logging

try:
    from logger_config import configure_logging
except ImportError:
    from .logger_config import configure_logging

configure_logging(logging.WARNING)

try:
    from main_app import create_app
except ImportError:
    from .main_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
