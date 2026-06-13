"""Unit tests for shared fix_nested worker functions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.shared.fix_nested.worker import (
    detect_nested_tags,
    download_svg_file,
    fix_nested_tags,
    upload_fixed_svg,
    verify_fix,
)


@pytest.fixture
def mock_copy_svg():
    with (
        patch("src.main_app.shared.fix_nested.worker.match_nested_tags") as m_match,
        patch("src.main_app.shared.fix_nested.worker.fix_nested_file") as m_fix,
    ):
        yield {"match": m_match, "fix": m_fix}


@pytest.fixture
def mock_api():
    with (
        patch("src.main_app.shared.fix_nested.worker.download_one_file") as m_down,
        patch("src.main_app.shared.fix_nested.worker.get_user_site") as m_site,
        patch("src.main_app.shared.fix_nested.worker.upload_file") as m_upload,
    ):
        yield {"down": m_down, "site": m_site, "upload": m_upload}


def test_download_svg_file_success(mock_api, tmp_path):
    mock_api["down"].return_value = {"result": "success", "path": str(tmp_path / "test.svg")}
    res = download_svg_file("Test.svg", tmp_path)
    assert res.ok is True
    assert res.path == tmp_path / "test.svg"


def test_download_svg_file_fail(mock_api, tmp_path):
    mock_api["down"].return_value = {"result": "error"}
    res = download_svg_file("Test.svg", tmp_path)
    assert res.ok is False
    assert res.error == "download_failed"


def test_detect_nested_tags(mock_copy_svg):
    mock_copy_svg["match"].return_value = ["tag1", "tag2"]
    res = detect_nested_tags(Path("test.svg"))
    assert res.count == 2
    assert res.tags == ["tag1", "tag2"]


def test_fix_nested_tags(mock_copy_svg):
    mock_copy_svg["fix"].return_value = True
    assert fix_nested_tags(Path("test.svg")) is True


def test_verify_fix(mock_copy_svg):
    mock_copy_svg["match"].return_value = ["tag1"]
    res = verify_fix(Path("test.svg"), before_count=3)
    assert res.before == 3
    assert res.after == 1
    assert res.fixed == 2


def test_upload_fixed_svg_no_user():
    res = upload_fixed_svg("Test.svg", Path("test.svg"), 2, None)
    assert res.ok is False
    assert res.error == "unauthenticated"


def test_upload_fixed_svg_auth_fail(mock_api):
    mock_api["site"].return_value = None
    res = upload_fixed_svg("Test.svg", Path("test.svg"), 2, {"id": 1})
    assert res.ok is False
    assert res.error == "oauth-auth-failed"


def test_upload_fixed_svg_success(mock_api):
    mock_api["site"].return_value = MagicMock()
    mock_api["upload"].return_value = {"result": "Success", "newrevid": 123}
    res = upload_fixed_svg("Test.svg", Path("test.svg"), 2, {"id": 1})
    assert res.ok is True


def test_upload_fixed_svg_fail(mock_api):
    mock_api["site"].return_value = MagicMock()
    mock_api["upload"].return_value = {"result": "Failure", "error": "ratelimited"}
    res = upload_fixed_svg("Test.svg", Path("test.svg"), 2, {"id": 1})
    assert res.ok is False
    assert res.error == "ratelimited"
