"""
Tests for explorer utility functions.
"""
import json
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch

import pytest

from src.app.app_routes.explorer.utils import (
    _validate_path_under_base,
    get_main_data,
    get_files_full_path,
    get_files,
    get_languages,
    get_temp_title,
    get_informations,
)


@pytest.fixture
def temp_svg_data_dir():
    """Create a temporary directory structure for svg_data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        with patch('src.app.app_routes.explorer.utils.svg_data_path', base_path):
            yield base_path


def test_validate_path_under_base(temp_svg_data_dir):
    """
    Tests the _validate_path_under_base function.
    """
    title_dir = temp_svg_data_dir / "title1"
    title_dir.mkdir()
    sub_dir = title_dir / "files"
    sub_dir.mkdir()

    # Valid path
    assert _validate_path_under_base("title1", "files") == sub_dir

    # Path traversal attempt
    with pytest.raises(PermissionError):
        _validate_path_under_base("title1", "../..")


def test_get_main_data(temp_svg_data_dir):
    """
    Tests the get_main_data function.
    """
    title_dir = temp_svg_data_dir / "title1"
    title_dir.mkdir()

    # File exists and is valid JSON
    json_path = title_dir / "files_stats.json"
    json_path.write_text('{"key": "value"}')
    assert get_main_data("title1") == {"key": "value"}

    # File does not exist
    assert get_main_data("nonexistent") == {}

    # File is not valid JSON
    json_path.write_text('this is not json')
    assert get_main_data("title1") == {}


def test_get_files_full_path(temp_svg_data_dir):
    """
    Tests the get_files_full_path function.
    """
    title_dir = temp_svg_data_dir / "title1" / "files"
    title_dir.mkdir(parents=True)
    (title_dir / "file1.txt").touch()
    (title_dir / "file2.svg").touch()

    files, path = get_files_full_path("title1", "files")
    assert set(files) == {"file1.txt", "file2.svg"}
    assert path == title_dir


def test_get_files(temp_svg_data_dir):
    """
    Tests the get_files function.
    """
    title_dir = temp_svg_data_dir / "title1" / "files"
    title_dir.mkdir(parents=True)
    (title_dir / "file1.txt").touch()
    (title_dir / "file2.svg").touch()

    files, path = get_files("title1", "files")
    assert files == ["file2.svg"]
    assert path == title_dir


def test_get_languages():
    """
    Tests the get_languages function.
    """
    translations_data = {
        "new": {
            "id1": {"fr": "Bonjour", "es": "Hola"},
            "id2": {"de": "Guten Tag"}
        }
    }
    assert get_languages("title1", translations_data) == ["de", "es", "fr"]
    assert get_languages("title1", {}) == []


def test_get_temp_title(temp_svg_data_dir):
    """
    Tests the get_temp_title function.
    """
    title_dir = temp_svg_data_dir / "title1"
    title_dir.mkdir()

    # title.txt exists
    (title_dir / "title.txt").write_text("Custom Title")
    assert get_temp_title("title1") == "Custom Title"

    # title.txt does not exist
    assert get_temp_title("nonexistent") == "nonexistent"
