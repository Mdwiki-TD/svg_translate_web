"""Unit tests for shared fix_nested files_service functions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.main_app.api_services.files_service.files_helpers import (
    download_svg_file,
    upload_fixed_svg,
)


@pytest.fixture
def mock_api(monkeypatch: pytest.MonkeyPatch):
    mocks = {
        "down": MagicMock(),
        "upload": MagicMock(),
    }
    monkeypatch.setattr(
        "src.main_app.api_services.files_service.files_helpers.download_one_file",
        mocks["down"],
    )
    monkeypatch.setattr(
        "src.main_app.api_services.files_service.files_helpers.upload_file",
        mocks["upload"],
    )
    return mocks


class TestDownloadSvgFile:
    def test_download_svg_file_no_user(self, mock_api):
        mock_api["down"].return_value = {"result": "failed", "msg": "", "path": ""}
        res = download_svg_file("Test.svg", Path("test.svg"))
        assert res.get("ok") is False
        assert res.get("error") == "download_failed"
        assert res.get("details") == {"msg": "", "path": "", "result": "failed"}

    def test_download_svg_file_success(self, mock_api, tmp_path):
        mock_api["down"].return_value = {"result": "success", "path": str(tmp_path / "test.svg")}
        res = download_svg_file("Test.svg", tmp_path)
        assert res.get("ok") is True
        assert res.get("path") == tmp_path / "test.svg"

    def test_download_svg_file_fail(self, mock_api, tmp_path):
        mock_api["down"].return_value = {"result": "error"}
        res = download_svg_file("Test.svg", tmp_path)
        assert res.get("ok") is False
        assert res.get("error") == "download_failed"


class TestUploadFixedSvg:
    def test_upload_fixed_svg_no_user(self, mock_site):
        res = upload_fixed_svg("Test.svg", Path("test.svg"), 2, mock_site)
        assert res.get("ok") is False
        assert res.get("error") == "File not found"
        assert res.get("details") is None

    def test_upload_fixed_svg_success(self, mock_api, mock_site):
        mock_api["upload"].return_value = {"result": "success", "newrevid": 123}
        res = upload_fixed_svg("Test.svg", Path("test.svg"), 2, mock_site)
        assert res.get("ok") is True

    def test_upload_fixed_svg_fail(self, mock_api, mock_site):
        mock_api["upload"].return_value = {"result": "Failure", "error": "ratelimited"}
        res = upload_fixed_svg("Test.svg", Path("test.svg"), 2, mock_site)
        assert res.get("ok") is False
        assert res.get("error") == "ratelimited"
