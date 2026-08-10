"""Tests for crop_main_files/download module."""

from unittest.mock import MagicMock

import pytest
import requests

from src.main_app.api_services.files_service import DownloadAndSaveData
from src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.steps.download import download_file_for_cropping


@pytest.fixture
def mock_download(monkeypatch):
    _mock = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.steps.download.download_and_save", _mock
    )
    return _mock


class TestDownloadFileForCropping:
    """Tests for download_file_for_cropping function."""

    def test_empty_filename_returns_error(self, tmp_path, mock_download):
        """Test that empty filename returns error."""
        result = download_file_for_cropping("", tmp_path)
        assert result["success"] is False
        assert result["error"] == "Empty filename"
        assert result["path"] is None

    def test_filename_without_file_prefix(self, tmp_path, mock_download):
        """Test downloading file without File: prefix."""
        mock_session = MagicMock(spec=requests.Session)
        mock_download.return_value = DownloadAndSaveData(result="success", path=str(tmp_path / "test.svg"))
        result = download_file_for_cropping("test.svg", tmp_path, mock_session)
        mock_download.assert_called_once_with(
            title="test.svg",
            out_dir=tmp_path,
            session=mock_session,
            overwrite_download=True,
        )
        assert result["success"] is True
        assert result["path"] == tmp_path / "test.svg"

    def test_filename_with_file_prefix(self, tmp_path, mock_download):
        """Test downloading file with File: prefix."""
        mock_session = MagicMock(spec=requests.Session)

        mock_download.return_value = DownloadAndSaveData(result="success", path=str(tmp_path / "test.svg"))
        result = download_file_for_cropping("File:test.svg", tmp_path, mock_session)
        mock_download.assert_called_once_with(
            title="test.svg",
            out_dir=tmp_path,
            session=mock_session,
            overwrite_download=True,
        )
        assert result["success"] is True

    def test_download_failure(self, tmp_path, mock_download):
        """Test handling of download failure."""
        mock_session = MagicMock(spec=requests.Session)
        mock_download.return_value = DownloadAndSaveData(result="failed")
        result = download_file_for_cropping("test.svg", tmp_path, mock_session)
        assert result["success"] is False
        assert "failed" in result["error"]

    def test_existing_file_result(self, tmp_path, mock_download):
        """Test handling of existing file result."""
        mock_session = MagicMock(spec=requests.Session)
        mock_download.return_value = DownloadAndSaveData(result="existing", path=str(tmp_path / "test.svg"))
        result = download_file_for_cropping("test.svg", tmp_path, mock_session)
        assert result["success"] is True
        assert result["path"] == tmp_path / "test.svg"

    def test_download_exception(self, tmp_path, mock_download):
        """Test handling of download exception."""
        mock_session = MagicMock(spec=requests.Session)
        mock_download.side_effect = Exception("Network error")
        result = download_file_for_cropping("test.svg", tmp_path, mock_session)
        assert result["success"] is False
        assert "Exception" in result["error"]
        assert "Network error" in result["error"]

    def test_no_session_provided(self, tmp_path, mock_download):
        """Test download without providing a session."""
        mock_download.return_value = DownloadAndSaveData(result="success", path=str(tmp_path / "test.svg"))
        result = download_file_for_cropping("test.svg", tmp_path)
        mock_download.assert_called_once_with(
            title="test.svg",
            out_dir=tmp_path,
            session=None,
            overwrite_download=True,
        )
        assert result["success"] is True
