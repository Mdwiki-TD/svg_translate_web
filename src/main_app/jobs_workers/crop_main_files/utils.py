"""
Utility functions for cropping main files.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_cropped_filename(filename: str) -> str:
    """
    Transform filename to cropped version.

    Examples:
        "File:death rate from obesity, World, 2021.svg"
        → "File:death rate from obesity, World, 2021 (cropped).svg"
    """
    if filename.startswith("File:"):
        base_name = filename[5:]
    else:
        base_name = filename

    path = Path(base_name)
    new_stem = f"{path.stem} (cropped)"
    new_filename = new_stem + path.suffix
    return f"File:{new_filename}"


__all__ = [
    "generate_cropped_filename",
]
