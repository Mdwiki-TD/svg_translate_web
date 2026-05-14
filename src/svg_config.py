"""
Central configuration for the SVG Translate web application.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

if os.getenv("APP_ENV") != "production":
    _env_file_path = str(Path(__file__).parent.parent.parent / ".env")
    load_dotenv(_env_file_path)

CopySVGTranslation_PATH = os.getenv("CopySVGTranslation_PATH", "")

try:
    import CopySVGTranslation  # type: ignore  # noqa: F401
except ImportError:
    if CopySVGTranslation_PATH and Path(CopySVGTranslation_PATH).is_dir():
        sys.path.insert(0, str(Path(CopySVGTranslation_PATH).parent))
