import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.main_app.app_routes.fix_nested.fix_utils import (
    create_task_folder, save_metadata, log_to_task, download_svg_file,
    detect_nested_tags, fix_nested_tags, verify_fix, upload_fixed_svg,
    process_fix_nested
)

@patch("src.app.app_routes.fix_nested.fix_utils.settings")
def test_create_task_folder(mock_settings, tmp_path):
    mock_settings.paths.fix_nested_data = tmp_path
    task_id = "t1"
    folder = create_task_folder(task_id)
    assert folder == tmp_path / task_id
    assert folder.exists()

def test_save_metadata(tmp_path):
    metadata = {"key": "value"}
    save_metadata(tmp_path, metadata)
    metadata_file = tmp_path / "metadata.json"
    assert metadata_file.exists()
    with open(metadata_file, "r") as f:
        assert json.load(f) == metadata

def test_log_to_task(tmp_path):
    log_to_task(tmp_path, "test message")
    log_file = tmp_path / "task_log.txt"
    assert log_file.exists()
    assert "test message" in log_file.read_text()

@patch("src.app.app_routes.fix_nested.fix_utils.download_one_file")
def test_download_svg_file_success(mock_download, tmp_path):
    mock_download.return_value = {"result": "success", "path": str(tmp_path / "file.svg")}
    res = download_svg_file("file.svg", tmp_path)
    assert res["ok"] is True
    assert res["path"] == tmp_path / "file.svg"

@patch("src.app.app_routes.fix_nested.fix_utils.match_nested_tags")
def test_detect_nested_tags(mock_match):
    mock_match.return_value = ["tag1", "tag2"]
    res = detect_nested_tags(Path("file.svg"))
    assert res["count"] == 2
    assert res["tags"] == ["tag1", "tag2"]

@patch("src.app.app_routes.fix_nested.fix_utils.fix_nested_file")
def test_fix_nested_tags(mock_fix):
    mock_fix.return_value = True
    assert fix_nested_tags(Path("file.svg")) is True

@patch("src.app.app_routes.fix_nested.fix_utils.match_nested_tags")
def test_verify_fix(mock_match):
    mock_match.return_value = ["remaining"]
    res = verify_fix(Path("file.svg"), 5)
    assert res["before"] == 5
    assert res["after"] == 1
    assert res["fixed"] == 4

@patch("src.app.app_routes.fix_nested.fix_utils.get_user_site")
@patch("src.app.app_routes.fix_nested.fix_utils.upload_file")
def test_upload_fixed_svg_success(mock_upload, mock_get_site):
    mock_get_site.return_value = MagicMock()
    mock_upload.return_value = {"result": "Success"}

    res = upload_fixed_svg("file.svg", Path("file.svg"), 5, {"user": "data"})
    assert res["ok"] is True

@patch("src.app.app_routes.fix_nested.fix_utils.download_svg_file")
@patch("src.app.app_routes.fix_nested.fix_utils.detect_nested_tags")
@patch("src.app.app_routes.fix_nested.fix_utils.fix_nested_tags")
@patch("src.app.app_routes.fix_nested.fix_utils.verify_fix")
@patch("src.app.app_routes.fix_nested.fix_utils.upload_fixed_svg")
def test_process_fix_nested_success(
    mock_upload, mock_verify, mock_fix, mock_detect, mock_download, tmp_path
):
    mock_download.return_value = {"ok": True, "path": Path("dummy.svg")}
    mock_detect.return_value = {"count": 5}
    mock_fix.return_value = True
    mock_verify.return_value = {"fixed": 5, "after": 0, "before": 5}
    mock_upload.return_value = {"ok": True, "result": {"result": "Success"}}

    res = process_fix_nested("file.svg", {"user": "data"})
    assert res["success"] is True
    assert "Successfully fixed" in res["message"]
