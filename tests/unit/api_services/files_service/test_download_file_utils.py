"""
Comprehensive unit tests for download_file_utils module.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.api_services.files_service.download_file_utils import download_one_file


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


class TestDownloadOneFile:
    def test_empty_title_returns_empty_result(self, temp_output_dir):
        result = download_one_file("", temp_output_dir, 0)
        assert result["result"] == ""

    def test_existing_file_skips_download(self, temp_output_dir):
        title = "test.svg"
        file_path = temp_output_dir / title
        file_path.write_text("existing content")
        result = download_one_file(title, temp_output_dir, 1)
        assert result["result"] == "existing"
        assert result["msg"] == "Skip existing file, no overwrite"
        assert result["path"] == str(file_path)

    def test_existing_file_overwrites(self, temp_output_dir, mock_download_core):
        title = "test.svg"
        file_path = temp_output_dir / title
        file_path.write_text("old content")
        mock_download_core.return_value = b"<svg>new</svg>"
        result = download_one_file(title, temp_output_dir, 1, overwrite=True)
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
            "src.main_app.api_services.files_service.download_file_utils.create_commons_session",
            lambda ua: mock_session,
        )
        result = download_one_file(title, temp_output_dir, 1)
        assert result["result"] == "success"

    def test_uses_provided_session(self, temp_output_dir, mock_download_core, mock_requests_session):
        title = "session_test.svg"
        mock_download_core.return_value = b"<svg>content</svg>"
        result = download_one_file(title, temp_output_dir, 1, session=mock_requests_session)
        assert result["result"] == "success"
