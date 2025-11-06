"""
Tests for thumbnail generation.
"""
from pathlib import Path
import tempfile

from src.app.app_routes.explorer.thumbnail_utils import save_thumb


def test_save_thumb_returns_false():
    """
    Tests that save_thumb currently returns False as it's not implemented.
    """
    with tempfile.NamedTemporaryFile(suffix=".svg") as src, \
         tempfile.NamedTemporaryFile(suffix=".png") as thumb:
        src_path = Path(src.name)
        thumb_path = Path(thumb.name)
        assert not save_thumb(src_path, thumb_path)
