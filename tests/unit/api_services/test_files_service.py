"""Unit tests for shared fix_nested files_service functions."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from src.main_app.api_services.files_service import (
    download_svg_file,
    upload_fixed_svg,
)


@pytest.fixture
def mock_api():
    with (
        patch("src.main_app.api_services.files_service.download_one_file") as m_down,
        patch("src.main_app.api_services.files_service.upload_file") as m_upload,
    ):
        yield {"down": m_down, "upload": m_upload}


class TestDownloadSvgFile:
    @pytest.mark.network
    def test_download_svg_file_no_user(self, mocker):
        mock_download = mocker.patch("src.main_app.api_services.files_service.download_one_file")
        mock_download.return_value = {"result": "failed", "msg": "", "path": ""}

        res = download_svg_file("Test.svg", Path("test.svg"))
        assert res.get("ok") is False
        assert res.get("error") == "download_failed"
        assert res.get("error_details") == {"msg": "", "path": "", "result": "failed"}

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
    @pytest.mark.network
    def test_upload_fixed_svg_no_user(self, mock_site, mocker):
        mock_upload = mocker.patch("src.main_app.api_services.files_service.upload_file")
        mock_upload.return_value = {"result": "Failure", "error": "File not found"}

        res = upload_fixed_svg("Test.svg", Path("test.svg"), 2, mock_site)
        assert res.get("ok") is False
        assert res.get("error") == "File not found"
        assert res.get("error_details") is None

    def test_upload_fixed_svg_success(self, mock_api, mock_site):
        mock_api["upload"].return_value = {"result": "Success", "newrevid": 123}
        res = upload_fixed_svg("Test.svg", Path("test.svg"), 2, mock_site)
        assert res.get("ok") is True

    def test_upload_fixed_svg_fail(self, mock_api, mock_site):
        mock_api["upload"].return_value = {"result": "Failure", "error": "ratelimited"}
        res = upload_fixed_svg("Test.svg", Path("test.svg"), 2, mock_site)
        assert res.get("ok") is False
        assert res.get("error") == "ratelimited"
