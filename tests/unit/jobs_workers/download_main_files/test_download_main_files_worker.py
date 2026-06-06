"""Unit tests for download_main_files_worker module."""

from __future__ import annotations

import threading
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers import download_main_files_worker


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch, mock_jobs_service):
    """Mock the services used by download_main_files_worker."""

    # Mock list_templates
    mock_list_templates = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.download_main_files_worker.list_templates", mock_list_templates)

    # Mock jobs_service (now accessed via base_worker)
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock(return_value="/tmp/job_1.json")
    mock_generate_result_file_name = MagicMock(side_effect=lambda job_id, job_type: f"{job_type}_job_{job_id}.json")
    monkeypatch.setattr("src.main_app.jobs_workers.base_worker.update_job_status", mock_update_job_status)
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name",
        mock_save_job_result,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.generate_result_file_name",
        mock_generate_result_file_name,
    )

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.paths.main_files_path = "/tmp/main_files"
    mock_settings.oauth = MagicMock()
    mock_settings.other.user_agent = "TestBot/1.0"
    mock_settings.jobs = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.download_main_files_worker.settings", mock_settings)

    return {
        "list_templates": mock_list_templates,
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "generate_result_file_name": mock_generate_result_file_name,
        "settings": mock_settings,
        "is_job_cancelled": mock_jobs_service,
    }


def test_download_file_from_commons_success(tmp_path, mock_services):
    """Test successful download of a file from Commons."""
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()

    # Mock requests.Session
    mock_response = Mock()
    mock_response.content = b"SVG file content"
    mock_response.raise_for_status = Mock()

    mock_session = Mock()
    mock_session.get.return_value = mock_response

    result = download_main_files_worker.download_file_from_commons(
        "test.svg",
        output_dir,
        session=mock_session,
    )

    assert result["success"] is True
    assert result["path"] == "test.svg"
    assert result["size_bytes"] == 16
    assert result["error"] is None
    assert (output_dir / "test.svg").exists()


def test_download_file_from_commons_empty_filename(tmp_path):
    """Test that empty filename is handled."""
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()

    result = download_main_files_worker.download_file_from_commons(
        "",
        output_dir,
    )

    assert result["success"] is False
    assert result["error"] == "Empty filename"


def test_download_file_from_commons_request_error(tmp_path):
    """Test handling of request errors."""
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()

    # Mock requests.Session with an error
    mock_session = Mock()
    mock_session.get.side_effect = requests.RequestException("Network error")

    result = download_main_files_worker.download_file_from_commons(
        "test.svg",
        output_dir,
        session=mock_session,
    )

    assert result["success"] is False
    assert "Download failed: Network error" in result["error"]


def test_download_file_from_commons_unexpected_error(tmp_path):
    """Test handling of unexpected errors."""
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()

    # Mock requests.Session with an unexpected error
    mock_response = Mock()
    mock_response.content = b"content"
    mock_response.raise_for_status = Mock()

    mock_session = Mock()
    mock_session.get.return_value = mock_response

    # Mock Path.write_bytes to raise an exception
    with patch("pathlib.Path.write_bytes", side_effect=OSError("Disk full")):
        result = download_main_files_worker.download_file_from_commons(
            "test.svg",
            output_dir,
            session=mock_session,
        )

    assert result["success"] is False
    assert "Unexpected error: Disk full" in result["error"]


def test_download_file_from_commons_creates_session_if_none():
    """Test that a session is created if none is provided."""
    with patch("src.main_app.jobs_workers.download_main_files_worker.requests.Session") as mock_session_class:
        mock_session = Mock()
        mock_response = Mock()
        mock_response.content = b"content"
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        with patch("pathlib.Path.write_bytes"):
            download_main_files_worker.download_file_from_commons(
                "test.svg",
                Path("/tmp/downloads"),
                session=None,
            )

        mock_session_class.assert_called_once()


def test_download_main_files_with_no_templates(mock_services):
    """Test download_main_files_for_templates when there are no templates."""
    mock_services["list_templates"].return_value = []

    download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)

    # Should update status to running, then completed
    assert mock_services["update_job_status"].call_count == 2
    mock_services["update_job_status"].assert_any_call(
        1, "running", "download_main_files_job_1.json", job_type="download_main_files"
    )

    # Should save result
    mock_services["save_job_result_by_name"].assert_called()
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 0


def test_download_main_files_skips_templates_without_main_file(mock_services):
    """Test that templates without main_file are skipped."""
    templates = [
        TemplateRecord(id=1, title="Template:Test1", main_file=None, last_world_file=None),
        TemplateRecord(id=2, title="Template:Test2", main_file="", last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates

    download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)

    # Should save result with 0 downloads
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 0


def test_download_main_files_downloads_template_with_main_file(mock_services, tmp_path):
    """Test that templates with main_file are downloaded."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["settings"].paths.main_files_path = str(tmp_path)

    # Mock requests
    mock_response = Mock()
    mock_response.content = b"SVG content"
    mock_response.raise_for_status = Mock()

    with patch("src.main_app.jobs_workers.download_main_files_worker.requests.Session") as mock_session_class:
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)

    # Should save result with success file
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 1
    assert result["summary"]["success"] == 1
    assert len(result["files_downloaded"]) == 1
    assert result["files_downloaded"][0]["filename"] == "test.svg"


def test_download_main_files_handles_download_failure(mock_services, tmp_path):
    """Test that download failures are handled gracefully."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["settings"].paths.main_files_path = str(tmp_path)

    # Mock requests with error
    with patch("src.main_app.jobs_workers.download_main_files_worker.requests.Session") as mock_session_class:
        mock_session = Mock()
        mock_session.get.side_effect = requests.RequestException("404 Not Found")
        mock_session_class.return_value = mock_session

        download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)

    # Should save result with failed file
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 1
    assert result["summary"]["failed"] == 1
    assert len(result["files_failed"]) == 1
    assert "Download failed" in result["files_failed"][0]["reason"]


def test_download_main_files_handles_exception(mock_services, tmp_path):
    """Test that exceptions are handled gracefully."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["settings"].paths.main_files_path = str(tmp_path)

    # Mock requests with unexpected exception
    with patch("src.main_app.jobs_workers.download_main_files_worker.requests.Session") as mock_session_class:
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Unexpected error")
        mock_session_class.return_value = mock_session

        download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)

    # Should save result with failed file
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 1
    assert result["summary"]["failed"] == 1
    assert len(result["files_failed"]) == 1
    assert "Unexpected error" in result["files_failed"][0]["reason"]


def test_download_main_files_processes_multiple_templates(mock_services, tmp_path):
    """Test processing multiple templates with mixed results."""
    templates = [
        TemplateRecord(id=1, title="Template:Test1", main_file="test1.svg", last_world_file=None),
        TemplateRecord(id=2, title="Template:Test2", main_file=None, last_world_file=None),
        TemplateRecord(id=3, title="Template:Test3", main_file="test3.svg", last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["settings"].paths.main_files_path = str(tmp_path)

    # Mock requests - first succeeds, third fails
    def get_side_effect(url, timeout, allow_redirects):
        if "test1" in url:
            mock_response = Mock()
            mock_response.content = b"SVG 1 content"
            mock_response.raise_for_status = Mock()
            return mock_response
        elif "test3" in url:
            raise requests.RequestException("404")

    with patch("src.main_app.jobs_workers.download_main_files_worker.requests.Session") as mock_session_class:
        mock_session = Mock()
        mock_session.get.side_effect = get_side_effect
        mock_session_class.return_value = mock_session

        download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)

    # Should save result with correct counts
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 2
    assert result["summary"]["success"] == 1
    assert result["summary"]["failed"] == 1
    assert len(result["files_downloaded"]) == 1
    assert len(result["files_failed"]) == 1


def test_download_main_files_respects_cancellation(mock_services, tmp_path):
    """Test that download respects cancellation event."""
    templates = [
        TemplateRecord(id=i, title=f"Template:Test{i}", main_file=f"test{i}.svg", last_world_file=None)
        for i in range(1, 21)
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["settings"].paths.main_files_path = str(tmp_path)

    cancel_event = threading.Event()
    cancel_event.set()  # Set immediately to cancel

    with patch("src.main_app.jobs_workers.download_main_files_worker.requests.Session"):
        download_main_files_worker.download_main_files_for_templates(job_id=1, user=None, cancel_event=cancel_event)

    # Should save result with cancelled status
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["status"] == "cancelled"
    assert "cancelled_at" in result


def test_download_main_files_handles_file_with_file_prefix(mock_services, tmp_path):
    """Test that files with 'File:' prefix are handled correctly."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file="File:test.svg", last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["settings"].paths.main_files_path = str(tmp_path)

    # Mock requests
    mock_response = Mock()
    mock_response.content = b"SVG content"
    mock_response.raise_for_status = Mock()

    with patch("src.main_app.jobs_workers.download_main_files_worker.requests.Session") as mock_session_class:
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)

    # Should download with cleaned filename
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["success"] == 1
    # The file should be saved as test.svg, not File:test.svg
    assert (tmp_path / "test.svg").exists()


def test_download_main_files_checks_if_file_exists(mock_services, tmp_path):
    """Test that existing files are counted."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["settings"].paths.main_files_path = str(tmp_path)

    # Create the file first
    (tmp_path / "test.svg").write_text("existing content")

    # Mock requests to download the file again
    mock_response = Mock()
    mock_response.content = b"new content"
    mock_response.raise_for_status = Mock()

    with patch("src.main_app.jobs_workers.download_main_files_worker.requests.Session") as mock_session_class:
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)

    # Should count as exists
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["success"] == 1


def test_download_main_files_fatal_error_handling(mock_services):
    """Test that fatal errors are handled properly."""
    # Make list_templates raise an exception
    mock_services["list_templates"].side_effect = Exception("Database error")

    download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)

    # Should update status to failed
    final_call = mock_services["update_job_status"].call_args
    assert final_call[0][1] == "failed"


def test_generate_main_files_zip_success(tmp_path, monkeypatch):
    """Test successful generation of zip file on disk."""
    # Create test files
    main_files_path = tmp_path / "main_files"
    main_files_path.mkdir()
    (main_files_path / "test1.svg").write_text("content1")
    (main_files_path / "test2.svg").write_text("content2")

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.paths.main_files_path = str(main_files_path)
    monkeypatch.setattr("src.main_app.jobs_workers.download_main_files_worker.settings", mock_settings)

    # Generate the zip file
    zip_path = download_main_files_worker.generate_main_files_zip()

    assert zip_path.exists()
    assert zip_path.name == "main_files.zip"

    # Verify the zip contents
    with zipfile.ZipFile(zip_path) as zf:
        assert "test1.svg" in zf.namelist()
        assert "test2.svg" in zf.namelist()
        assert len(zf.namelist()) == 2


def test_generate_main_files_zip_no_files(tmp_path, monkeypatch):
    """Test generating zip when directory has no files."""
    # Create empty directory
    main_files_path = tmp_path / "main_files"
    main_files_path.mkdir()

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.paths.main_files_path = str(main_files_path)
    monkeypatch.setattr("src.main_app.jobs_workers.download_main_files_worker.settings", mock_settings)

    # Should raise RuntimeError when no files found
    with pytest.raises(RuntimeError, match="No files found to zip"):
        download_main_files_worker.generate_main_files_zip()


def test_generate_main_files_zip_directory_not_exists(tmp_path, monkeypatch):
    """Test generating zip when directory doesn't exist."""
    # Use a non-existent directory
    main_files_path = tmp_path / "nonexistent"

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.paths.main_files_path = str(main_files_path)
    monkeypatch.setattr("src.main_app.jobs_workers.download_main_files_worker.settings", mock_settings)

    # Should raise FileNotFoundError
    with pytest.raises(FileNotFoundError):
        download_main_files_worker.generate_main_files_zip()


def test_generate_main_files_zip_excludes_self(tmp_path, monkeypatch):
    """Test that the zip file excludes itself."""
    # Create test files
    main_files_path = tmp_path / "main_files"
    main_files_path.mkdir()
    (main_files_path / "test1.svg").write_text("content1")

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.paths.main_files_path = str(main_files_path)
    monkeypatch.setattr("src.main_app.jobs_workers.download_main_files_worker.settings", mock_settings)

    # Generate the zip file
    zip_path = download_main_files_worker.generate_main_files_zip()

    # Verify the zip does not include itself
    with zipfile.ZipFile(zip_path) as zf:
        assert "test1.svg" in zf.namelist()
        assert "main_files.zip" not in zf.namelist()
        assert len(zf.namelist()) == 1


def test_create_main_files_zip_success(tmp_path, monkeypatch):
    """Test successful serving of existing zip file."""
    # Create test files and pre-generate zip
    main_files_path = tmp_path / "main_files"
    main_files_path.mkdir()
    (main_files_path / "test1.svg").write_text("content1")
    (main_files_path / "test2.svg").write_text("content2")

    # Pre-generate the zip file
    zip_path = main_files_path / "main_files.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(main_files_path / "test1.svg", "test1.svg")
        zf.write(main_files_path / "test2.svg", "test2.svg")

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.paths.main_files_path = str(main_files_path)
    monkeypatch.setattr("src.main_app.jobs_workers.download_main_files_worker.settings", mock_settings)

    # Mock send_file to return a mock response
    with patch("src.main_app.jobs_workers.download_main_files_worker.send_file") as mock_send:
        mock_response = Mock()
        mock_send.return_value = mock_response

        response, status_code = download_main_files_worker.create_main_files_zip()

        assert status_code == 200
        assert response == mock_response

        # Verify send_file was called with the correct arguments
        call_args = mock_send.call_args
        assert call_args[0][0] == zip_path
        assert call_args[1]["mimetype"] == "application/zip"
        assert call_args[1]["as_attachment"] is True
        assert call_args[1]["download_name"] == "main_files.zip"


def test_create_main_files_zip_not_found(tmp_path, monkeypatch):
    """Test serving zip when file doesn't exist."""
    # Create directory but no zip file
    main_files_path = tmp_path / "main_files"
    main_files_path.mkdir()
    (main_files_path / "test1.svg").write_text("content1")

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.paths.main_files_path = str(main_files_path)
    monkeypatch.setattr("src.main_app.jobs_workers.download_main_files_worker.settings", mock_settings)

    response, status_code = download_main_files_worker.create_main_files_zip()

    assert status_code == 404
    assert "Please run a 'Download Main Files' job first" in response


def test_create_main_files_zip_directory_not_exists(tmp_path, monkeypatch):
    """Test creating zip when directory doesn't exist."""
    # Use a non-existent directory
    main_files_path = tmp_path / "nonexistent"

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.paths.main_files_path = str(main_files_path)
    monkeypatch.setattr("src.main_app.jobs_workers.download_main_files_worker.settings", mock_settings)

    response, status_code = download_main_files_worker.create_main_files_zip()

    assert status_code == 404
    assert response == "Main files directory does not exist"


def test_create_main_files_zip_empty_file(tmp_path, monkeypatch):
    """Test serving zip when file is empty/corrupted."""
    # Create directory with empty zip file
    main_files_path = tmp_path / "main_files"
    main_files_path.mkdir()
    zip_path = main_files_path / "main_files.zip"
    zip_path.write_text("")  # Empty file

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.paths.main_files_path = str(main_files_path)
    monkeypatch.setattr("src.main_app.jobs_workers.download_main_files_worker.settings", mock_settings)

    response, status_code = download_main_files_worker.create_main_files_zip()

    assert status_code == 500
    assert "Zip file is empty or corrupted" in response


def test_create_main_files_zip_empty_directory(tmp_path, monkeypatch):
    """Test serving zip when directory has no files (but zip exists)."""
    # Create an empty directory with pre-existing zip
    main_files_path = tmp_path / "main_files"
    main_files_path.mkdir()

    # Create empty zip file
    zip_path = main_files_path / "main_files.zip"
    with zipfile.ZipFile(zip_path, "w"):
        pass  # Empty zip

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.paths.main_files_path = str(main_files_path)
    monkeypatch.setattr("src.main_app.jobs_workers.download_main_files_worker.settings", mock_settings)

    # Mock send_file to return a mock response
    with patch("src.main_app.jobs_workers.download_main_files_worker.send_file") as mock_send:
        mock_response = Mock()
        mock_send.return_value = mock_response

        response, status_code = download_main_files_worker.create_main_files_zip()

        assert status_code == 200
        assert response == mock_response
        mock_send.assert_called_once()


def test_create_main_files_zip_ignores_subdirectories(tmp_path, monkeypatch):
    """Test that subdirectories are not included in the zip."""
    # Create files and a subdirectory
    main_files_path = tmp_path / "main_files"
    main_files_path.mkdir()
    (main_files_path / "test1.svg").write_text("content1")
    subdir = main_files_path / "subdir"
    subdir.mkdir()
    (subdir / "test2.svg").write_text("content2")

    # Pre-generate zip file with only top-level files
    zip_path = main_files_path / "main_files.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(main_files_path / "test1.svg", "test1.svg")

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.paths.main_files_path = str(main_files_path)
    monkeypatch.setattr("src.main_app.jobs_workers.download_main_files_worker.settings", mock_settings)

    # Mock send_file to return a mock response
    with patch("src.main_app.jobs_workers.download_main_files_worker.send_file") as mock_send:
        mock_response = Mock()
        mock_send.return_value = mock_response

        response, status_code = download_main_files_worker.create_main_files_zip()

        assert status_code == 200
        assert response == mock_response
        mock_send.assert_called_once()


def test_download_main_files_saves_progress_periodically(mock_services, tmp_path):
    """Test that progress is saved periodically during downloads."""
    # Create 15 templates to ensure periodic saves
    templates = [
        TemplateRecord(id=i, title=f"Template:Test{i}", main_file=f"test{i}.svg", last_world_file=None)
        for i in range(1, 16)
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["settings"].paths.main_files_path = str(tmp_path)

    # Mock requests
    mock_response = Mock()
    mock_response.content = b"SVG content"
    mock_response.raise_for_status = Mock()

    with patch("src.main_app.jobs_workers.download_main_files_worker.requests.Session") as mock_session_class:
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)

    # Should save progress at least twice (at n=1 and n=10)
    assert mock_services["save_job_result_by_name"].call_count >= 2


def test_download_file_from_commons_url_encoding(tmp_path):
    """Test that filenames with spaces are properly URL-encoded."""
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()

    mock_response = Mock()
    mock_response.content = b"content"
    mock_response.raise_for_status = Mock()

    mock_session = Mock()
    mock_session.get.return_value = mock_response

    download_main_files_worker.download_file_from_commons(
        "test file with spaces.svg",
        output_dir,
        session=mock_session,
    )

    # Verify the URL was properly encoded
    called_url = mock_session.get.call_args[0][0]
    assert "test_file_with_spaces.svg" in called_url or "test%20file%20with%20spaces.svg" in called_url


def test_download_file_from_commons_http_error_404(tmp_path):
    """Test handling of 404 HTTP errors."""
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()

    mock_session = Mock()
    mock_session.get.side_effect = requests.HTTPError("404 Not Found")

    result = download_main_files_worker.download_file_from_commons(
        "nonexistent.svg",
        output_dir,
        session=mock_session,
    )

    assert result["success"] is False
    assert "Download failed" in result["error"]


def test_download_main_files_creates_output_directory(mock_services, tmp_path):
    """Test that output directory is created if it doesn't exist."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates

    # Use a non-existent directory
    output_dir = tmp_path / "nonexistent_dir"
    mock_services["settings"].paths.main_files_path = str(output_dir)

    # Mock requests
    mock_response = Mock()
    mock_response.content = b"SVG content"
    mock_response.raise_for_status = Mock()

    with patch("src.main_app.jobs_workers.download_main_files_worker.requests.Session") as mock_session_class:
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)

    # Verify the directory was created
    assert output_dir.exists()


def test_download_main_files_handles_job_deletion_during_final_status_update(mock_services, tmp_path):
    """Test that final status update handles job deletion gracefully."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["settings"].paths.main_files_path = str(tmp_path)

    # Mock requests
    mock_response = Mock()
    mock_response.content = b"SVG content"
    mock_response.raise_for_status = Mock()

    # Make the final status update raise LookupError
    def update_status_side_effect(job_id, status, result_file=None, job_type=None):
        if status == "completed":
            raise LookupError("Job was deleted")

    mock_services["update_job_status"].side_effect = update_status_side_effect

    with patch("src.main_app.jobs_workers.download_main_files_worker.requests.Session") as mock_session_class:
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        # Should not raise an exception
        download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)


def test_download_file_from_commons_with_special_characters(tmp_path):
    """Test downloading files with special characters in the filename."""
    output_dir = tmp_path / "downloads"
    output_dir.mkdir()

    mock_response = Mock()
    mock_response.content = b"content"
    mock_response.raise_for_status = Mock()

    mock_session = Mock()
    mock_session.get.return_value = mock_response

    result = download_main_files_worker.download_file_from_commons(
        "test-file_v2.0.svg",
        output_dir,
        session=mock_session,
    )

    assert result["success"] is True
    assert (output_dir / "test-file_v2.0.svg").exists()


def test_download_main_files_generates_zip_on_completion(mock_services, tmp_path):
    """Test that zip file is generated automatically when job completes successfully."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["settings"].paths.main_files_path = str(tmp_path)

    # Mock requests
    mock_response = Mock()
    mock_response.content = b"SVG content"
    mock_response.raise_for_status = Mock()

    with patch("src.main_app.jobs_workers.download_main_files_worker.requests.Session") as mock_session_class:
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)

    # Verify zip file was generated
    zip_path = tmp_path / "main_files.zip"
    assert zip_path.exists()

    # Verify zip contains the success file
    with zipfile.ZipFile(zip_path) as zf:
        assert "test.svg" in zf.namelist()


def test_download_main_files_no_zip_on_failure(mock_services, tmp_path):
    """Test that zip file is not generated when job fails."""
    # Make list_templates raise an exception to cause job failure
    mock_services["list_templates"].side_effect = Exception("Database error")
    mock_services["settings"].paths.main_files_path = str(tmp_path)

    download_main_files_worker.download_main_files_for_templates(job_id=1, user=None)

    # Verify zip file was NOT generated (job failed)
    zip_path = tmp_path / "main_files.zip"
    assert not zip_path.exists()


def test_download_main_files_for_templates_accepts_args_keyword_param(mock_services):
    """Test that download_main_files_for_templates accepts args= keyword-only param (unified signature)."""
    mock_services["list_templates"].return_value = []

    # Should not raise TypeError; args is accepted but unused
    download_main_files_worker.download_main_files_for_templates(job_id=1, user=None, args={"some_key": "value"})

    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 0


def test_download_main_files_for_templates_args_defaults_to_none(mock_services):
    """Test that args defaults to None and entry point works without it."""
    mock_services["list_templates"].return_value = []

    # Call without args param - should use None default
    download_main_files_worker.download_main_files_for_templates(job_id=99, user=None)

    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 0


class TestDownloadMainFilesWorkerInitialization:
    """Tests for DownloadMainFilesWorker initialization."""

    def test_worker_reads_limit_items_from_args(self, mock_services):
        """Test worker reads limit_items from args."""
        worker = download_main_files_worker.DownloadMainFilesWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"limit_items": 5},
        )

        assert worker.limit_items == 5

    def test_worker_defaults_limit_items_when_args_none(self, mock_services):
        """Test worker defaults limit_items to 0 when args is None."""
        worker = download_main_files_worker.DownloadMainFilesWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args=None,
        )

        assert worker.limit_items == 0

    def test_worker_limit_items_none_when_key_missing(self, mock_services):
        """Test worker sets limit_items to None when args has no limit_items key."""
        worker = download_main_files_worker.DownloadMainFilesWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"other_key": "value"},
        )

        assert worker.limit_items is None


class TestDownloadMainFilesWorkerApplyLimits:
    """Tests for _apply_limits method."""

    def test_apply_limits_with_limit_set(self, mock_services):
        """Test _apply_limits truncates list when limit is set."""
        templates = [
            TemplateRecord(id=i, title=f"Template:T{i}", main_file=f"f{i}.svg", last_world_file=None)
            for i in range(1, 4)
        ]

        worker = download_main_files_worker.DownloadMainFilesWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"limit_items": 2},
        )
        result = worker._apply_limits(templates)

        assert len(result) == 2

    def test_apply_limits_with_zero_limit(self, mock_services):
        """Test _apply_limits returns all items when limit is 0."""
        templates = [
            TemplateRecord(id=1, title="Template:T1", main_file="f1.svg", last_world_file=None),
            TemplateRecord(id=2, title="Template:T2", main_file="f2.svg", last_world_file=None),
        ]

        worker = download_main_files_worker.DownloadMainFilesWorker(
            job_id=1,
            user=None,
            cancel_event=None,
        )
        result = worker._apply_limits(templates)

        assert len(result) == 2

    def test_apply_limits_with_limit_greater_than_list(self, mock_services):
        """Test _apply_limits returns all items when limit exceeds list size."""
        templates = [
            TemplateRecord(id=1, title="Template:T1", main_file="f1.svg", last_world_file=None),
        ]

        worker = download_main_files_worker.DownloadMainFilesWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"limit_items": 10},
        )
        result = worker._apply_limits(templates)

        assert len(result) == 1

    def test_apply_limits_with_non_integer_limit(self, mock_services):
        """Test _apply_limits treats non-integer limit as 0."""
        templates = [
            TemplateRecord(id=1, title="Template:T1", main_file="f1.svg", last_world_file=None),
            TemplateRecord(id=2, title="Template:T2", main_file="f2.svg", last_world_file=None),
        ]

        worker = download_main_files_worker.DownloadMainFilesWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"limit_items": "not_int"},
        )
        result = worker._apply_limits(templates)

        assert len(result) == 2


class TestDownloadMainFilesEntryPointArgsMapping:
    """Tests for download_main_files_limit_items -> limit_items mapping in entry point."""

    def test_entry_point_maps_download_main_files_limit_items(self, mock_services):
        """Test that download_main_files_limit_items is mapped to limit_items."""
        mock_services["list_templates"].return_value = []

        with patch("src.main_app.jobs_workers.download_main_files_worker.DownloadMainFilesWorker") as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            download_main_files_worker.download_main_files_for_templates(
                job_id=1,
                user=None,
                args={"download_main_files_limit_items": 10},
            )

        # args is the 4th positional arg: (job_id, user, cancel_event, args)
        passed_args = MockWorker.call_args[0][3]
        assert passed_args["limit_items"] == 10

    def test_entry_point_does_not_map_when_key_absent(self, mock_services):
        """Test that args are passed unchanged when key is absent."""
        mock_services["list_templates"].return_value = []

        with patch("src.main_app.jobs_workers.download_main_files_worker.DownloadMainFilesWorker") as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            download_main_files_worker.download_main_files_for_templates(
                job_id=1,
                user=None,
                args={"other_key": "value"},
            )

        passed_args = MockWorker.call_args[0][3]
        assert "limit_items" not in passed_args

    def test_entry_point_does_not_map_when_value_falsy(self, mock_services):
        """Test that mapping is skipped when value is falsy."""
        mock_services["list_templates"].return_value = []

        for falsy_value in [0, None, "", False]:
            with patch("src.main_app.jobs_workers.download_main_files_worker.DownloadMainFilesWorker") as MockWorker:
                mock_instance = MagicMock()
                MockWorker.return_value = mock_instance

                download_main_files_worker.download_main_files_for_templates(
                    job_id=1,
                    user=None,
                    args={"download_main_files_limit_items": falsy_value},
                )

            passed_args = MockWorker.call_args[0][3]
            assert "limit_items" not in passed_args, f"Should not map for falsy value: {falsy_value!r}"

    def test_entry_point_does_not_modify_args_when_none(self, mock_services):
        """Test that entry point works correctly when args is None."""
        mock_services["list_templates"].return_value = []

        with patch("src.main_app.jobs_workers.download_main_files_worker.DownloadMainFilesWorker") as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            download_main_files_worker.download_main_files_for_templates(job_id=1, user=None, args=None)

        passed_args = MockWorker.call_args[0][3]
        assert passed_args is None
