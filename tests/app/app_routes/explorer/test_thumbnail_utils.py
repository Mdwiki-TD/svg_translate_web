"""
Tests for thumbnail generation.
"""
from pathlib import Path
import tempfile

from src.app.app_routes.explorer import thumbnail_utils


def test_save_thumb_returns_false(tmp_path: Path) -> None:
    source = tmp_path / "image.svg"
    target = tmp_path / "thumb.svg"

    source.write_text("<svg/>", encoding="utf-8")

    assert thumbnail_utils.save_thumb(source, target) is False


def test_save_thumb_returns_false2():
    """
    Tests that save_thumb currently returns False as it's not implemented.
    """
    with tempfile.NamedTemporaryFile(suffix=".svg") as src, \
            tempfile.NamedTemporaryFile(suffix=".png") as thumb:
        src_path = Path(src.name)
        thumb_path = Path(thumb.name)
        assert not thumbnail_utils.save_thumb(src_path, thumb_path)
