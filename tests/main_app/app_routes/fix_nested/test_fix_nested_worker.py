from pathlib import Path
from unittest.mock import MagicMock, patch

from src.main_app.app_routes.fix_nested.worker import (
    detect_nested_tags,
    download_svg_file,
    fix_nested_tags,
    process_fix_nested,
    upload_fixed_svg,
    verify_fix,
)


@patch("src.main_app.app_routes.fix_nested.worker.download_one_file")
def test_download_svg_file_success(mock_download, tmp_path):
    mock_download.return_value = {"result": "success", "path": str(tmp_path / "file.svg")}
    res = download_svg_file("file.svg", tmp_path)
    assert res["ok"] is True
    assert res["path"] == tmp_path / "file.svg"


@patch("src.main_app.app_routes.fix_nested.worker.match_nested_tags")
def test_detect_nested_tags(mock_match):
    mock_match.return_value = ["tag1", "tag2"]
    res = detect_nested_tags(Path("file.svg"))
    assert res["count"] == 2
    assert res["tags"] == ["tag1", "tag2"]


@patch("src.main_app.app_routes.fix_nested.worker.fix_nested_file")
def test_fix_nested_tags(mock_fix):
    mock_fix.return_value = True
    assert fix_nested_tags(Path("file.svg")) is True


@patch("src.main_app.app_routes.fix_nested.worker.match_nested_tags")
def test_verify_fix(mock_match):
    mock_match.return_value = ["remaining"]
    res = verify_fix(Path("file.svg"), 5)
    assert res["before"] == 5
    assert res["after"] == 1
    assert res["fixed"] == 4


@patch("src.main_app.app_routes.fix_nested.worker.get_user_site")
@patch("src.main_app.app_routes.fix_nested.worker.upload_file")
def test_upload_fixed_svg_success(mock_upload, mock_get_site):
    mock_get_site.return_value = MagicMock()
    mock_upload.return_value = {"result": "Success"}

    res = upload_fixed_svg("file.svg", Path("file.svg"), 5, {"user": "data"})
    assert res["ok"] is True


@patch("src.main_app.app_routes.fix_nested.worker.download_svg_file")
@patch("src.main_app.app_routes.fix_nested.worker.detect_nested_tags")
@patch("src.main_app.app_routes.fix_nested.worker.fix_nested_tags")
@patch("src.main_app.app_routes.fix_nested.worker.verify_fix")
@patch("src.main_app.app_routes.fix_nested.worker.upload_fixed_svg")
def test_process_fix_nested_success(mock_upload, mock_verify, mock_fix, mock_detect, mock_download, tmp_path):
    mock_download.return_value = {"ok": True, "path": Path("dummy.svg")}
    mock_detect.return_value = {"count": 5}
    mock_fix.return_value = True
    mock_verify.return_value = {"fixed": 5, "after": 0, "before": 5}
    mock_upload.return_value = {"ok": True, "result": {"result": "Success"}}

    res = process_fix_nested("file.svg", {"user": "data"})
    assert res["success"] is True
    assert "Successfully fixed" in res["message"]


# --- Additional tests for uncovered paths ---


@patch("src.main_app.app_routes.fix_nested.worker.download_one_file")
def test_download_svg_file_failure(mock_download, tmp_path):
    """download_svg_file returns ok=False when download fails."""
    mock_download.return_value = {"result": "error", "error": "not_found"}
    res = download_svg_file("missing.svg", tmp_path)
    assert res["ok"] is False
    assert res["error"] == "download_failed"


@patch("src.main_app.app_routes.fix_nested.worker.match_nested_tags")
def test_detect_nested_tags_empty(mock_match):
    """detect_nested_tags returns count=0 for file with no nested tags."""
    mock_match.return_value = []
    res = detect_nested_tags(Path("clean.svg"))
    assert res["count"] == 0
    assert res["tags"] == []


@patch("src.main_app.app_routes.fix_nested.worker.fix_nested_file")
def test_fix_nested_tags_returns_false(mock_fix):
    """fix_nested_tags returns False when fix_nested_file returns falsy."""
    mock_fix.return_value = False
    assert fix_nested_tags(Path("file.svg")) is False


@patch("src.main_app.app_routes.fix_nested.worker.match_nested_tags")
def test_verify_fix_all_fixed(mock_match):
    """verify_fix reports all tags fixed when after_count is 0."""
    mock_match.return_value = []
    res = verify_fix(Path("file.svg"), 3)
    assert res["before"] == 3
    assert res["after"] == 0
    assert res["fixed"] == 3


@patch("src.main_app.app_routes.fix_nested.worker.get_user_site")
def test_upload_fixed_svg_no_user(mock_get_site):
    """upload_fixed_svg returns unauthenticated error when user is None/falsy."""
    res = upload_fixed_svg("file.svg", Path("file.svg"), 2, None)
    assert res["ok"] is False
    assert res["error"] == "unauthenticated"
    mock_get_site.assert_not_called()


@patch("src.main_app.app_routes.fix_nested.worker.get_user_site")
def test_upload_fixed_svg_no_site(mock_get_site):
    """upload_fixed_svg returns oauth error when site is None."""
    mock_get_site.return_value = None
    res = upload_fixed_svg("file.svg", Path("file.svg"), 2, {"user": "data"})
    assert res["ok"] is False
    assert res["error"] == "oauth-auth-failed"


@patch("src.main_app.app_routes.fix_nested.worker.get_user_site")
@patch("src.main_app.app_routes.fix_nested.worker.upload_file")
def test_upload_fixed_svg_upload_failure(mock_upload, mock_get_site):
    """upload_fixed_svg returns ok=False when upload result is not 'Success'."""
    mock_get_site.return_value = MagicMock()
    mock_upload.return_value = {"result": "Failure", "error": "upload_error"}
    res = upload_fixed_svg("file.svg", Path("file.svg"), 2, {"user": "data"})
    assert res["ok"] is False
    assert res["error"] == "upload_error"


@patch("src.main_app.app_routes.fix_nested.worker.download_svg_file")
def test_process_fix_nested_download_fails(mock_download):
    """process_fix_nested returns failure when download fails."""
    mock_download.return_value = {"ok": False, "error": "download_failed"}
    res = process_fix_nested("bad.svg", {"user": "data"})
    assert res["success"] is False
    assert "Failed to download" in res["message"]


@patch("src.main_app.app_routes.fix_nested.worker.download_svg_file")
@patch("src.main_app.app_routes.fix_nested.worker.detect_nested_tags")
def test_process_fix_nested_no_nested_tags(mock_detect, mock_download):
    """process_fix_nested returns failure when no nested tags found."""
    mock_download.return_value = {"ok": True, "path": Path("dummy.svg")}
    mock_detect.return_value = {"count": 0}
    res = process_fix_nested("clean.svg", {"user": "data"})
    assert res["success"] is False
    assert "No nested tags found" in res["message"]


@patch("src.main_app.app_routes.fix_nested.worker.download_svg_file")
@patch("src.main_app.app_routes.fix_nested.worker.detect_nested_tags")
@patch("src.main_app.app_routes.fix_nested.worker.fix_nested_tags")
def test_process_fix_nested_fix_fails(mock_fix, mock_detect, mock_download):
    """process_fix_nested returns failure when fix_nested_tags fails."""
    mock_download.return_value = {"ok": True, "path": Path("dummy.svg")}
    mock_detect.return_value = {"count": 3}
    mock_fix.return_value = False
    res = process_fix_nested("broken.svg", {"user": "data"})
    assert res["success"] is False
    assert "Failed to fix" in res["message"]


@patch("src.main_app.app_routes.fix_nested.worker.download_svg_file")
@patch("src.main_app.app_routes.fix_nested.worker.detect_nested_tags")
@patch("src.main_app.app_routes.fix_nested.worker.fix_nested_tags")
@patch("src.main_app.app_routes.fix_nested.worker.verify_fix")
def test_process_fix_nested_no_tags_fixed(mock_verify, mock_fix, mock_detect, mock_download):
    """process_fix_nested returns failure when verify shows zero tags fixed."""
    mock_download.return_value = {"ok": True, "path": Path("dummy.svg")}
    mock_detect.return_value = {"count": 3}
    mock_fix.return_value = True
    mock_verify.return_value = {"fixed": 0, "after": 3, "before": 3}
    res = process_fix_nested("stubborn.svg", {"user": "data"})
    assert res["success"] is False
    assert "No nested tags were fixed" in res["message"]


@patch("src.main_app.app_routes.fix_nested.worker.download_svg_file")
@patch("src.main_app.app_routes.fix_nested.worker.detect_nested_tags")
@patch("src.main_app.app_routes.fix_nested.worker.fix_nested_tags")
@patch("src.main_app.app_routes.fix_nested.worker.verify_fix")
@patch("src.main_app.app_routes.fix_nested.worker.upload_fixed_svg")
def test_process_fix_nested_upload_fails(mock_upload, mock_verify, mock_fix, mock_detect, mock_download):
    """process_fix_nested returns failure when upload fails after successful fix."""
    mock_download.return_value = {"ok": True, "path": Path("dummy.svg")}
    mock_detect.return_value = {"count": 2}
    mock_fix.return_value = True
    mock_verify.return_value = {"fixed": 2, "after": 0, "before": 2}
    mock_upload.return_value = {"ok": False, "error": "upload_failed", "error_details": "Timeout"}
    res = process_fix_nested("file.svg", {"user": "data"})
    assert res["success"] is False
    assert "upload failed" in res["message"]
