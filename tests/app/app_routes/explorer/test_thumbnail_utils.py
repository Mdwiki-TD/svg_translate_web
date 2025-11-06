"""Tests for thumbnail utilities."""

from pathlib import Path

from src.app.app_routes.explorer import thumbnail_utils


def test_save_thumb_returns_false(tmp_path: Path) -> None:
    source = tmp_path / "image.svg"
    target = tmp_path / "thumb.svg"

    source.write_text("<svg/>", encoding="utf-8")

    assert thumbnail_utils.save_thumb(source, target) is False
