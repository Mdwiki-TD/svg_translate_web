import json
import os
from unittest.mock import mock_open, patch

import pytest

from src.main_app.tasks.tasks_utils import commons_link, json_save, make_results_summary, save_files_stats


def test_json_save(tmp_path):
    # Test valid save
    data = {"key": "value"}
    file_path = tmp_path / "test.json"
    json_save(file_path, data)

    assert file_path.exists()
    with open(file_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == data

    # Test empty data
    log_mock = patch("src.main_app.tasks.tasks_utils.logger")
    with log_mock as mock_logger:
        json_save(file_path, {})
        mock_logger.error.assert_called()

    # Test exception handling (e.g., directory not exists)
    # json_save doesn't create parent dirs itself based on current implementation details
    # (commented out in source), but let's try a permission error or invalid path
    with patch("builtins.open", side_effect=OSError("Permission denied")):
        with log_mock as mock_logger:
            json_save("dummy", data)
            mock_logger.error.assert_called()


def test_commons_link():
    # Basic
    link = commons_link("File:Test.svg")
    assert "href='https://commons.wikimedia.org/wiki/File:Test.svg'" in link
    assert ">File:Test.svg</a>" in link

    # With name
    link2 = commons_link("File:Test.svg", name="My Link")
    assert ">My Link</a>" in link2

    # Special chars
    link3 = commons_link("File:A & B.svg")
    assert "A%20%26%20B.svg" in link3
    assert "A &amp; B.svg" in link3


def test_save_files_stats(tmp_path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    data = {"stats": 1}

    save_files_stats(data, out_dir)

    expected_file = out_dir / "files_stats.json"
    assert expected_file.exists()
    with open(expected_file, "r", encoding="utf-8") as f:
        assert json.load(f) == data


def test_make_results_summary():
    res = make_results_summary(
        len_files=10,
        files_to_upload_count=5,
        no_file_path=2,
        injects_result={"nested_files": 1, "success": 8, "failed": 1},
        translations={"new": {"a": 1, "b": 2}},
        main_title="File:Main.svg",
        upload_result={"uploaded": 5},
    )

    assert res["total_files"] == 10
    assert res["files_to_upload_count"] == 5
    assert res["no_file_path"] == 2
    assert res["injects_result"]["nested_files"] == 1
    assert res["injects_result"]["success"] == 8
    assert res["injects_result"]["failed"] == 1
    assert res["new_translations_count"] == 2
    assert res["upload_result"]["uploaded"] == 5
    assert res["main_title"] == "File:Main.svg"
