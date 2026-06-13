"""Unit tests for shared fix_nested files_service functions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.shared.fix_nested.files_service import (
    download_svg_file,
    upload_fixed_svg,
)


@pytest.fixture
def mock_api():
    with (
        patch("src.main_app.shared.fix_nested.files_service.download_one_file") as m_down,
        patch("src.main_app.shared.fix_nested.files_service.get_user_site") as m_site,
        patch("src.main_app.shared.fix_nested.files_service.upload_file") as m_upload,
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
