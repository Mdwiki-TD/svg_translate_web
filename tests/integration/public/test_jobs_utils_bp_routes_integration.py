"""Integration tests for the admin jobs management routes."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from werkzeug.wrappers import Response


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch):
    _mock = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_utils_bp.settings", _mock)
    return _mock


@pytest.fixture
def mock_send_from_directory(monkeypatch: pytest.MonkeyPatch) -> Mock:
    _mock = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_utils_bp.send_from_directory", _mock)
    return _mock


@pytest.fixture
def mock_create_main_files_zip(monkeypatch: pytest.MonkeyPatch) -> Mock:
    _mock = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_utils_bp.create_main_files_zip", _mock)
    return _mock


@pytest.fixture
def mock_flash(monkeypatch: pytest.MonkeyPatch) -> Mock:
    _mock = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_utils_bp.flash", _mock)
    return _mock


class TestCropMainFilesRoutes:
    """
    tests for /jobs_utils/crop-main-files/... routes
    serve_crop_original_file
    serve_crop_cropped_file
    compare_crop_files
    """


class TestDownloadMainFilesRoutes:
    """tests for /jobs_utils/download_main_files/... routes"""

    def test_serve_download_main_file(self, mock_settings, mock_send_from_directory, admin_jobs_client, tmp_path):
        """Test serving a downloaded main file."""

        main_files_path = str(tmp_path / "main_files")
        mock_settings.paths.main_files_path = main_files_path

        mock_send_from_directory.return_value = Response("file_content")

        response = admin_jobs_client.get("/jobs_utils/download_main_files/file/test.svg")
        assert response.status_code == 200

        mock_send_from_directory.assert_called_once_with(main_files_path, "test.svg")

    def test_download_all_main_files(self, mock_create_main_files_zip, admin_jobs_client):
        """Test downloading all main files as zip."""

        mock_create_main_files_zip.return_value = ("zip_content", 200)

        response = admin_jobs_client.get("/jobs_utils/download_main_files/download-all")
        assert response.status_code == 200

        mock_create_main_files_zip.assert_called_once()

    def test_download_all_main_files_no_zip(self, mock_create_main_files_zip, mock_flash, admin_jobs_client):
        """Test downloading all main files when zip doesn't exist - should redirect with flash."""

        mock_create_main_files_zip.return_value = ("Please run a 'Download Main Files' job first", 404)

        response = admin_jobs_client.get("/jobs_utils/download_main_files/download-all", follow_redirects=True)
        # Should redirect to jobs list page with flash message
        assert response.status_code == 200
        mock_flash.assert_called_once_with("Please run a 'Download Main Files' job first", "warning")

        mock_create_main_files_zip.assert_called_once()

    def test_download_all_main_files_error(self, mock_create_main_files_zip, mock_flash, admin_jobs_client):
        """Test downloading all main files when zip is corrupted - should redirect with flash."""

        mock_create_main_files_zip.return_value = ("Zip file is empty or corrupted", 500)

        response = admin_jobs_client.get("/jobs_utils/download_main_files/download-all", follow_redirects=True)
        # Should redirect to jobs list page with flash message
        assert response.status_code == 200
        mock_flash.assert_called_once_with("Zip file is empty or corrupted", "danger")

        mock_create_main_files_zip.assert_called_once()

    def test_serve_download_main_file_with_path_traversal_attempt(self, admin_jobs_client):
        """Test that path traversal is handled by send_from_directory."""

        # send_from_directory should handle path traversal attempts
        with patch("src.main_app.public.jobs_utils_bp.send_from_directory") as mock_send:
            mock_send.return_value = Response("safe response")
            response = admin_jobs_client.get("/jobs_utils/download_main_files/file/../../../etc/passwd")
            assert response.status_code == 404
