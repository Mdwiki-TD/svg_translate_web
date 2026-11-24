"""Unit tests for download_main_files zip_utils module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.main_app.jobs_workers.admin_jobs_workers.download_main_files.zip_utils import (
    MAIN_FILES_ZIP_NAME,
    ZipProvider,
)


class TestCreateMainFilesZip:
    def test_directory_not_exists(self):
        result, status = ZipProvider(main_files_path=Path("/_znonexistent")).create_main_files_zip()
        assert status == 404
        assert "Main files directory does not exist" in result

    def test_zip_not_found(self, tmp_path):

        result, status = ZipProvider(main_files_path=tmp_path).create_main_files_zip()
        assert status == 404
        assert "Zip file not found" in result

    def test_zip_empty(self, tmp_path):
        zip_path = tmp_path / MAIN_FILES_ZIP_NAME
        zip_path.write_text("")

        result, status = ZipProvider(main_files_path=tmp_path).create_main_files_zip()
        assert status == 500
        assert "empty or corrupted" in result

    @patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.zip_utils.send_file")
    def test_zip_found_returns_file(self, mock_send_file, tmp_path):
        zip_path = tmp_path / MAIN_FILES_ZIP_NAME
        zip_path.write_bytes(b"PK\x03\x04fake zip content")

        mock_send_file.return_value = MagicMock()
        result, status = ZipProvider(main_files_path=tmp_path).create_main_files_zip()
        assert status == 200
        mock_send_file.assert_called_once()
