"""
Comprehensive unit tests for download_file_utils module.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.main_app.api_services.clients.commons_client import GetWithRetryData
from src.main_app.api_services.files_service.download_file_utils import (
    download_one_file,
    download_svg_file,
)


@pytest.fixture
def mock_requests_session():
    session = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.content = b"<svg>test</svg>"
    session.get.return_value = response
    return session


@pytest.fixture
def temp_output_dir(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_download_core(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr(
        "src.main_app.api_services.files_service.downloader.CommonsSession.get_with_retry_obj",
        _mock,
    )
    return _mock


class TestDownloadSvgFile:

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch: pytest.MonkeyPatch):
        self.mock_down = MagicMock()
        monkeypatch.setattr(
            "src.main_app.api_services.files_service.download_file_utils.download_one_file",
            self.mock_down,
        )

    def test_download_svg_file_no_user(self):
        self.mock_down.return_value = {"result": "failed", "msg": "", "path": ""}
        res = download_svg_file("Test.svg", Path("test.svg"))
        assert res.get("ok") is False
        assert res.get("error") == "download_failed"
        assert res.get("details") == {"msg": "", "path": "", "result": "failed"}

    def test_download_svg_file_success(self, tmp_path):
        self.mock_down.return_value = {"result": "success", "path": str(tmp_path / "test.svg")}
        res = download_svg_file("Test.svg", tmp_path)
        assert res.get("ok") is True
        assert res.get("path") == tmp_path / "test.svg"

    def test_download_svg_file_fail(self, tmp_path):
        self.mock_down.return_value = {"result": "error"}
        res = download_svg_file("Test.svg", tmp_path)
        assert res.get("ok") is False
        assert res.get("error") == "download_failed"


class TestDownloadOneFile:
    def test_empty_title_returns_empty_result(self, temp_output_dir):
        result = download_one_file("", temp_output_dir)
        assert result["result"] == "failed"

    def test_existing_file_skips_download(self, temp_output_dir):
        title = "test.svg"
        file_path = temp_output_dir / title
        file_path.write_text("existing content")
        result = download_one_file(title, temp_output_dir, 1, overwrite_download=False)
        assert result["result"] == "existing"
        assert result["msg"] == "Skip existing file, no overwrite"
        assert result["path"] == str(file_path)

    def test_existing_file_overwrites(self, temp_output_dir, mock_download_core):
        title = "test.svg"
        file_path = temp_output_dir / title
        file_path.write_text("old content")
        mock_download_core.return_value = GetWithRetryData(content=b"<svg>new</svg>", success=True, status_code=200)
        result = download_one_file(title, temp_output_dir, overwrite_download=True)
        assert result["result"] == "success"
        assert file_path.read_bytes() == b"<svg>new</svg>"

    def test_download_success(self, temp_output_dir, mock_download_core):
        title = "new_file.svg"
        mock_download_core.return_value = GetWithRetryData(content=b"<svg>content</svg>", success=True, status_code=200)
        result = download_one_file(title, temp_output_dir)
        assert result["result"] == "success"
        assert result["path"].endswith(title)
        assert (temp_output_dir / title).read_bytes() == b"<svg>content</svg>"

    def test_download_fails_empty_content(self, temp_output_dir, mock_download_core):
        title = "empty.svg"
        mock_download_core.return_value = GetWithRetryData(content=None, success=True, status_code=200)
        result = download_one_file(title, temp_output_dir)
        assert result["result"] == "failed"

    def test_download_fails_404(self, temp_output_dir, mock_download_core):
        title = "missing.svg"
        mock_download_core.return_value = GetWithRetryData(
            content=None, success=False, status_code=404, msg="Not found"
        )
        result = download_one_file(title, temp_output_dir)
        assert result["result"] == "failed"
        assert result["msg"] == "Not found"

    def test_download_fails_generic(self, temp_output_dir, mock_download_core):
        title = "error.svg"
        mock_download_core.side_effect = Exception("Connection timeout")
        result = download_one_file(title, temp_output_dir)
        assert result["result"] == "failed"
        assert result["msg"] is None

    def test_save_fails(self, temp_output_dir, mock_download_core, monkeypatch):
        title = "fail_save.svg"
        mock_download_core.return_value = GetWithRetryData(content=b"<svg>content</svg>", success=True, status_code=200)

        def mock_write_bytes(self, content):
            raise OSError("Disk full")

        monkeypatch.setattr("pathlib.Path.write_bytes", mock_write_bytes)
        result = download_one_file(title, temp_output_dir)
        assert result["result"] == "failed"
        assert "Failed to save file" in result["msg"]

    def test_creates_session_when_none(self, temp_output_dir, mock_download_core, monkeypatch):
        title = "session_test.svg"
        mock_download_core.return_value = GetWithRetryData(content=b"<svg>content</svg>", success=True, status_code=200)
        mock_session = MagicMock()
        monkeypatch.setattr(
            "src.main_app.api_services.clients.commons_client.create_commons_session",
            lambda ua: mock_session,
        )
        result = download_one_file(title, temp_output_dir)
        assert result["result"] == "success"

    def test_uses_provided_session(self, temp_output_dir, mock_download_core, mock_requests_session):
        title = "session_test.svg"
        mock_download_core.return_value = GetWithRetryData(content=b"<svg>content</svg>", success=True, status_code=200)
        result = download_one_file(title, temp_output_dir, session=mock_requests_session)
        assert result["result"] == "success"
