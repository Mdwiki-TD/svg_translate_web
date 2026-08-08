"""
Comprehensive unit tests for download_file_utils module.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from src.main_app.api_services.files_service.download_file_utils import (
    BASE_COMMONS_URL,
    download_commons_file_core,
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
        "src.main_app.api_services.files_service.download_file_utils.download_file_rate_limit",
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
        result = download_one_file("", temp_output_dir, 0)
        assert result["result"] == ""

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
        mock_download_core.return_value = b"<svg>new</svg>"
        result = download_one_file(title, temp_output_dir, 1, overwrite_download=True)
        assert result["result"] == "success"
        assert file_path.read_bytes() == b"<svg>new</svg>"

    def test_download_success(self, temp_output_dir, mock_download_core):
        title = "new_file.svg"
        mock_download_core.return_value = b"<svg>content</svg>"
        result = download_one_file(title, temp_output_dir, 1)
        assert result["result"] == "success"
        assert result["path"].endswith(title)
        assert (temp_output_dir / title).read_bytes() == b"<svg>content</svg>"

    def test_download_fails_empty_content(self, temp_output_dir, mock_download_core):
        title = "empty.svg"
        mock_download_core.return_value = None
        result = download_one_file(title, temp_output_dir, 1)
        assert result["result"] == "failed"

    def test_download_fails_404(self, temp_output_dir, mock_download_core):
        title = "missing.svg"
        mock_download_core.side_effect = Exception("404 Client Error: Not Found for url")
        result = download_one_file(title, temp_output_dir, 1)
        assert result["result"] == "failed"
        assert result["msg"] == "File not found"

    def test_download_fails_generic(self, temp_output_dir, mock_download_core):
        title = "error.svg"
        mock_download_core.side_effect = Exception("Connection timeout")
        result = download_one_file(title, temp_output_dir, 1)
        assert result["result"] == "failed"
        assert result["msg"] == ""

    def test_save_fails(self, temp_output_dir, mock_download_core, monkeypatch):
        title = "fail_save.svg"
        mock_download_core.return_value = b"<svg>content</svg>"

        def mock_write_bytes(self, content):
            raise OSError("Disk full")

        monkeypatch.setattr("pathlib.Path.write_bytes", mock_write_bytes)
        result = download_one_file(title, temp_output_dir, 1)
        assert result["result"] == "failed"
        assert "Failed to save file" in result["msg"]

    def test_creates_session_when_none(self, temp_output_dir, mock_download_core, monkeypatch):
        title = "session_test.svg"
        mock_download_core.return_value = b"<svg>content</svg>"
        mock_session = MagicMock()
        monkeypatch.setattr(
            "src.main_app.api_services.clients.commons_client.create_commons_session",
            lambda ua: mock_session,
        )
        result = download_one_file(title, temp_output_dir, 1)
        assert result["result"] == "success"

    def test_uses_provided_session(self, temp_output_dir, mock_download_core, mock_requests_session):
        title = "session_test.svg"
        mock_download_core.return_value = b"<svg>content</svg>"
        result = download_one_file(title, temp_output_dir, 1, session=mock_requests_session)
        assert result["result"] == "success"


class TestDownloadCommonsFileCore:
    """Tests for download_commons_file_core function."""

    def test_successful_download(self):
        """Test successful file download."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"<svg>test</svg>"
        session.request.return_value = mock_response

        result = download_commons_file_core("Test.svg", session)

        assert result == b"<svg>test</svg>"
        expected_url = f"{BASE_COMMONS_URL}Test.svg"
        session.request.assert_called_once_with(
            method="GET",
            data=None,
            params=None,
            url=expected_url,
            timeout=60,
            allow_redirects=True,
        )

    def test_spaces_converted_to_underscores(self):
        """Test that spaces in filename are converted to underscores."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"content"
        session.request.return_value = mock_response

        download_commons_file_core("My File.svg", session)

        expected_url = f"{BASE_COMMONS_URL}My_File.svg"
        session.request.assert_called_once_with(
            method="GET",
            data=None,
            params=None,
            url=expected_url,
            timeout=60,
            allow_redirects=True,
        )

    def test_custom_timeout(self):
        """Test custom timeout is passed through."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"content"
        session.request.return_value = mock_response

        download_commons_file_core("Test.svg", session, timeout=30)

        session.request.assert_called_once()
        call_kwargs = session.request.call_args[1]
        assert call_kwargs["timeout"] == 30

    def test_http_error_raises_exception(self):
        """Test that HTTP errors raise exceptions."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        session.request.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            download_commons_file_core("Missing.svg", session)

    def test_network_error_raises_exception(self):
        """Test that network errors raise exceptions."""
        session = MagicMock()
        session.request.side_effect = requests.ConnectionError("Connection refused")

        with pytest.raises(requests.ConnectionError):
            download_commons_file_core("Test.svg", session)

    def test_timeout_error_raises_exception(self):
        """Test that timeouts raise exceptions."""
        session = MagicMock()
        session.request.side_effect = requests.Timeout("Request timed out")

        with pytest.raises(requests.Timeout):
            download_commons_file_core("Test.svg", session)

    def test_filename_is_url_encoded(self):
        """Test that special characters in filename are URL encoded."""
        session = MagicMock()
        mock_response = MagicMock()
        mock_response.content = b"content"
        session.request.return_value = mock_response

        download_commons_file_core("File (with parens).svg", session)

        expected_url = f"{BASE_COMMONS_URL}File_%28with_parens%29.svg"
        session.request.assert_called_once_with(
            method="GET",
            data=None,
            params=None,
            url=expected_url,
            timeout=60,
            allow_redirects=True,
        )
