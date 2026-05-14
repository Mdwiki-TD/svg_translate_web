"""
# isort:skip_file
WSGI development entry point for the app.
"""

from __future__ import annotations
import logging
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

from logger_config import configure_logging

_env_file_path = str(Path(__file__).parent.parent.parent / ".env")
load_dotenv(_env_file_path)

CopySVGTranslation_PATH = os.getenv("CopySVGTranslation_PATH", "")

try:
    import CopySVGTranslation  # type: ignore  # noqa: F401
except ImportError:
    if CopySVGTranslation_PATH and Path(CopySVGTranslation_PATH).is_dir():
        sys.path.insert(0, str(Path(CopySVGTranslation_PATH).parent))

configure_logging(logging.DEBUG)

try:
    from main_app import create_app
except ImportError:
    from .main_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
