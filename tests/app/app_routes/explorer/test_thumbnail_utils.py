"""
Tests for thumbnail generation.
"""
import tempfile
from pathlib import Path

from src.app.app_routes.explorer import thumbnail_utils


def test_save_thumb_returns_false2():
    """
    Tests that save_thumb currently returns False as it's not implemented.
    """
    with tempfile.NamedTemporaryFile(suffix=".svg") as src, tempfile.NamedTemporaryFile(suffix=".png") as thumb:
        src_path = Path(src.name)
        thumb_path = Path(thumb.name)
        assert not thumbnail_utils.save_thumb(src_path, thumb_path)
