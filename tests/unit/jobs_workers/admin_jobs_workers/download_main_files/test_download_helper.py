"""Unit tests for download_main_files download_helper module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.admin_jobs_workers.download_main_files.download_helper import download_file_from_commons


@pytest.fixture
def mock_download_core(monkeypatch: pytest.MonkeyPatch):
    """Mock the services used by download_main_files worker."""
    _mock = MagicMock(return_value=b"svg-content")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.download_helper.download_commons_file_core",
        _mock,
    )

    return _mock


@pytest.fixture
def mock_session():
    return MagicMock()


class TestDownloadFileFromCommons:
    def test_download_file_from_commons_success(self, mock_download_core, tmp_path, mock_session):
        """Test successful file download."""
        output_dir = tmp_path
        filename = "Test.svg"

        result = download_file_from_commons(filename, output_dir, mock_session)

        assert result["success"] is True
        assert result["path"] == "Test.svg"
        assert result["size_bytes"] == len(b"svg-content")
        assert (output_dir / "Test.svg").read_bytes() == b"svg-content"

    def test_download_file_from_commons_failure(self, mock_download_core, tmp_path, mock_session):
        """Test handled download failure."""
        mock_download_core.side_effect = Exception("API Error")

        result = download_file_from_commons("Error.svg", tmp_path, mock_session)

        assert result["success"] is False
        assert "Download failed" in result["error"]
