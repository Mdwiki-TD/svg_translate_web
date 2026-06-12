"""Svg viewer"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def save_thumb(file_path: Path, file_thumb_path: Path, size: int = 300) -> bool:
    """Generate a thumbnail from an SVG file"""
    # TODO: make svg thumb
    return False


__all__ = [
    "save_thumb",
]
