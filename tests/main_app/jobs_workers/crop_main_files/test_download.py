"""Tests for crop_main_files/download module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.main_app.jobs_workers.crop_main_files.download import download_file_for_cropping


class TestDownloadFileForCropping:
    """Tests for download_file_for_cropping function."""

    def test_empty_filename_returns_error(self, tmp_path):
        """Test that empty filename returns error."""
        result = download_file_for_cropping("", tmp_path)
        assert result["success"] is False
        assert result["error"] == "Empty filename"
        assert result["path"] is None

    def test_filename_without_file_prefix(self, tmp_path):
        """Test downloading file without File: prefix."""
        mock_session = MagicMock(spec=requests.Session)
        with patch("src.main_app.jobs_workers.crop_main_files.download.download_one_file") as mock_download:
            mock_download.return_value = {
                "result": "success",
                "path": str(tmp_path / "test.svg"),
            }
            result = download_file_for_cropping("test.svg", tmp_path, mock_session)
            mock_download.assert_called_once_with(
                title="test.svg",
                out_dir=tmp_path,
                i=1,
                session=mock_session,
                overwrite=True,
            )
            assert result["success"] is True
            assert result["path"] == tmp_path / "test.svg"

    def test_filename_with_file_prefix(self, tmp_path):
        """Test downloading file with File: prefix."""
        mock_session = MagicMock(spec=requests.Session)
        with patch("src.main_app.jobs_workers.crop_main_files.download.download_one_file") as mock_download:
            mock_download.return_value = {
                "result": "success",
                "path": str(tmp_path / "test.svg"),
            }
            result = download_file_for_cropping("File:test.svg", tmp_path, mock_session)
            mock_download.assert_called_once_with(
                title="test.svg",
                out_dir=tmp_path,
                i=1,
                session=mock_session,
                overwrite=True,
            )
            assert result["success"] is True

    def test_download_failure(self, tmp_path):
        """Test handling of download failure."""
        mock_session = MagicMock(spec=requests.Session)
        with patch("src.main_app.jobs_workers.crop_main_files.download.download_one_file") as mock_download:
            mock_download.return_value = {
                "result": "failed",
            }
            result = download_file_for_cropping("test.svg", tmp_path, mock_session)
            assert result["success"] is False
            assert "failed" in result["error"]

    def test_existing_file_result(self, tmp_path):
        """Test handling of existing file result."""
        mock_session = MagicMock(spec=requests.Session)
        with patch("src.main_app.jobs_workers.crop_main_files.download.download_one_file") as mock_download:
            mock_download.return_value = {
                "result": "existing",
                "path": str(tmp_path / "test.svg"),
            }
            result = download_file_for_cropping("test.svg", tmp_path, mock_session)
            assert result["success"] is True
            assert result["path"] == tmp_path / "test.svg"

    def test_download_exception(self, tmp_path):
        """Test handling of download exception."""
        mock_session = MagicMock(spec=requests.Session)
        with patch("src.main_app.jobs_workers.crop_main_files.download.download_one_file") as mock_download:
            mock_download.side_effect = Exception("Network error")
            result = download_file_for_cropping("test.svg", tmp_path, mock_session)
            assert result["success"] is False
            assert "Exception" in result["error"]
            assert "Network error" in result["error"]

    def test_no_session_provided(self, tmp_path):
        """Test download without providing a session."""
        with patch("src.main_app.jobs_workers.crop_main_files.download.download_one_file") as mock_download:
            mock_download.return_value = {
                "result": "success",
                "path": str(tmp_path / "test.svg"),
            }
            result = download_file_for_cropping("test.svg", tmp_path)
            mock_download.assert_called_once_with(
                title="test.svg",
                out_dir=tmp_path,
                i=1,
                session=None,
                overwrite=True,
            )
            assert result["success"] is True
