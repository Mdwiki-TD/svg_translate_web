"""Integration tests for the admin jobs management routes."""

from __future__ import annotations

from unittest.mock import Mock, patch

from werkzeug.wrappers import Response

@patch("src.main_app.public.jobs_utils_bp.send_from_directory")
@patch("src.main_app.public.jobs_utils_bp.settings")
def test_serve_download_main_file(mock_settings, mock_send, admin_jobs_client, tmp_path):
    """Test serving a downloaded main file."""

    main_files_path = str(tmp_path / "main_files")
    mock_settings.paths.main_files_path = main_files_path

    mock_response = Response("file_content")
    mock_send.return_value = mock_response

    response = admin_jobs_client.get("/jobs_utils/download_main_files/file/test.svg")
    assert response.status_code == 200

    mock_send.assert_called_once_with(main_files_path, "test.svg")


@patch("src.main_app.public.jobs_utils_bp.create_main_files_zip")
def test_download_all_main_files(mock_create_zip, admin_jobs_client):
    """Test downloading all main files as zip."""

    mock_create_zip.return_value = ("zip_content", 200)

    response = admin_jobs_client.get("/jobs_utils/download_main_files/download-all")
    assert response.status_code == 200

    mock_create_zip.assert_called_once()


@patch("src.main_app.public.jobs_utils_bp.create_main_files_zip")
def test_download_all_main_files_no_zip(mock_create_zip, admin_jobs_client, monkeypatch):
    """Test downloading all main files when zip doesn't exist - should redirect with flash."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_utils_bp.flash", mock_flash)

    mock_create_zip.return_value = ("Please run a 'Download Main Files' job first", 404)

    response = admin_jobs_client.get("/jobs_utils/download_main_files/download-all", follow_redirects=True)
    # Should redirect to jobs list page with flash message
    assert response.status_code == 200
    mock_flash.assert_called_once_with("Please run a 'Download Main Files' job first", "warning")

    mock_create_zip.assert_called_once()


@patch("src.main_app.public.jobs_utils_bp.create_main_files_zip")
def test_download_all_main_files_error(mock_create_zip, admin_jobs_client, monkeypatch):
    """Test downloading all main files when zip is corrupted - should redirect with flash."""

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.public.jobs_utils_bp.flash", mock_flash)

    mock_create_zip.return_value = ("Zip file is empty or corrupted", 500)

    response = admin_jobs_client.get("/jobs_utils/download_main_files/download-all", follow_redirects=True)
    # Should redirect to jobs list page with flash message
    assert response.status_code == 200
    mock_flash.assert_called_once_with("Zip file is empty or corrupted", "danger")

    mock_create_zip.assert_called_once()


def test_serve_download_main_file_with_path_traversal_attempt(admin_jobs_client, mock_jobs_db):
    """Test that path traversal is handled by send_from_directory."""

    # send_from_directory should handle path traversal attempts
    with patch("src.main_app.public.jobs_utils_bp.send_from_directory") as mock_send:
        mock_send.return_value = Response("safe response")
        response = admin_jobs_client.get("/jobs_utils/download_main_files/file/../../../etc/passwd")
        assert response.status_code == 404
