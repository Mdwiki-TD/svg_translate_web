"""Unit tests for download_main_files runner module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner import (
    MAIN_FILES_ZIP_NAME,
    create_main_files_zip,
)


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner.settings",
        _mock,
    )
    return _mock


class TestCreateMainFilesZip:
    def test_directory_not_exists(self, mock_settings):

        mock_settings.paths.main_files_path = "/nonexistent/path"

        result, status = create_main_files_zip()
        assert status == 404
        assert "does not exist" in result

    def test_zip_not_found(self, mock_settings, tmp_path):

        mock_settings.paths.main_files_path = str(tmp_path)

        result, status = create_main_files_zip()
        assert status == 404
        assert "Zip file not found" in result

    def test_zip_empty(self, mock_settings, tmp_path):
        zip_path = tmp_path / MAIN_FILES_ZIP_NAME
        zip_path.write_text("")

        mock_settings.paths.main_files_path = str(tmp_path)

        result, status = create_main_files_zip()
        assert status == 500
        assert "empty or corrupted" in result

    @patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner.send_file")
    def test_zip_found_returns_file(self, mock_send_file, mock_settings, tmp_path):
        zip_path = tmp_path / MAIN_FILES_ZIP_NAME
        zip_path.write_bytes(b"PK\x03\x04fake zip content")

        mock_settings.paths.main_files_path = str(tmp_path)

        mock_send_file.return_value = MagicMock()
        result, status = create_main_files_zip()
        assert status == 200
        mock_send_file.assert_called_once()
