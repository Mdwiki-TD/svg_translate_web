"""Unit tests for crop_main_files.process module."""

from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.main_app.jobs_workers.crop_main_files import process
from src.main_app.template_service import TemplateRecord


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    """Mock the services used by process module."""

    # Mock template_service
    mock_list_templates = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process.template_service.list_templates", mock_list_templates
    )

    # Mock jobs_service
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process.jobs_service.update_job_status", mock_update_job_status
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process.jobs_service.save_job_result_by_name", mock_save_job_result
    )

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.download.dev_limit = 0  # No limit in tests
    mock_settings.oauth = MagicMock()
    mock_settings.oauth.user_agent = "TestBot/1.0"
    monkeypatch.setattr("src.main_app.jobs_workers.crop_main_files.process.settings", mock_settings)

    # Mock create_commons_session
    mock_create_session = MagicMock(return_value=Mock())
    monkeypatch.setattr("src.main_app.jobs_workers.crop_main_files.process.create_commons_session", mock_create_session)

    return {
        "list_templates": mock_list_templates,
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "settings": mock_settings,
        "create_commons_session": mock_create_session,
    }


def test_upload_one_success(mock_services):
    """Test successful upload of a cropped file."""
    job_id = 1
    file_info = {
        "cropped_filename": "File:test (cropped).svg",
        "cropped_path": Path("/tmp/test_cropped.svg"),
        "status": "pending",
    }
    user = {"username": "testuser"}
    result = {
        "summary": {
            "uploaded": 0,
            "failed": 0,
        }
    }

    with patch("src.main_app.jobs_workers.crop_main_files.process.upload_cropped_file") as mock_upload:
        mock_upload.return_value = {"success": True}

        process.upload_one(job_id, file_info, user, result)

    assert file_info["status"] == "uploaded"
    assert result["summary"]["uploaded"] == 1
    assert result["summary"]["failed"] == 0


def test_upload_one_failure(mock_services):
    """Test failed upload of a cropped file."""
    job_id = 1
    file_info = {
        "cropped_filename": "File:test (cropped).svg",
        "cropped_path": Path("/tmp/test_cropped.svg"),
        "status": "pending",
    }
    user = {"username": "testuser"}
    result = {
        "summary": {
            "uploaded": 0,
            "failed": 0,
        }
    }

    with patch("src.main_app.jobs_workers.crop_main_files.process.upload_cropped_file") as mock_upload:
        mock_upload.return_value = {"success": False, "error": "Upload failed: Network error"}

        process.upload_one(job_id, file_info, user, result)

    assert file_info["status"] == "failed"
    assert file_info["reason"] == "upload_failed"
    assert "Network error" in file_info["error"]
    assert result["summary"]["uploaded"] == 0
    assert result["summary"]["failed"] == 1


def test_upload_one_skips_if_no_path():
    """Test upload is not attempted if cropped_path is None."""
    job_id = 1
    file_info = {
        "cropped_filename": "File:test (cropped).svg",
        "cropped_path": None,
        "status": "pending",
    }
    user = {"username": "testuser"}
    result = {
        "summary": {
            "uploaded": 0,
            "failed": 0,
        }
    }

    with patch("src.main_app.jobs_workers.crop_main_files.process.upload_cropped_file") as mock_upload:
        process.upload_one(job_id, file_info, user, result)

    # Upload should not be called if no path
    mock_upload.assert_not_called()


def test_process_one_success(mock_services, tmp_path):
    """Test successful processing of one template."""
    job_id = 1
    template = TemplateRecord(
        id=1,
        title="Template:Test",
        last_world_file="File:test.svg",
        main_file=None,
    )
    result = {
        "summary": {
            "processed": 0,
            "cropped": 0,
            "failed": 0,
        }
    }
    temp_dir = tmp_path
    session = Mock()

    with (
        patch("src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping") as mock_download,
        patch("src.main_app.jobs_workers.crop_main_files.process.crop_svg_file") as mock_crop,
        patch("src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename") as mock_generate,
    ):

        mock_download.return_value = {"success": True, "path": tmp_path / "test.svg"}
        mock_crop.return_value = {"success": True}
        mock_generate.return_value = "File:test (cropped).svg"

        file_info = process.process_one(job_id, template, result, temp_dir, session)

    assert file_info["status"] != "failed"
    assert file_info["template_id"] == 1
    assert file_info["template_title"] == "Template:Test"
    assert file_info["original_file"] == "File:test.svg"
    assert file_info["cropped_filename"] == "File:test (cropped).svg"
    assert result["summary"]["processed"] == 1
    assert result["summary"]["cropped"] == 1


def test_process_one_download_failure(mock_services, tmp_path):
    """Test handling of download failure."""
    job_id = 1
    template = TemplateRecord(
        id=1,
        title="Template:Test",
        last_world_file="File:test.svg",
        main_file=None,
    )
    result = {
        "summary": {
            "processed": 0,
            "cropped": 0,
            "failed": 0,
        }
    }
    temp_dir = tmp_path
    session = Mock()

    with patch("src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping") as mock_download:
        mock_download.return_value = {"success": False, "error": "404 Not Found"}

        file_info = process.process_one(job_id, template, result, temp_dir, session)

    assert file_info["status"] == "failed"
    assert file_info["reason"] == "download_failed"
    assert "404 Not Found" in file_info["error"]
    assert result["summary"]["failed"] == 1


def test_process_one_crop_failure(mock_services, tmp_path):
    """Test handling of crop failure."""
    job_id = 1
    template = TemplateRecord(
        id=1,
        title="Template:Test",
        last_world_file="File:test.svg",
        main_file=None,
    )
    result = {
        "summary": {
            "processed": 0,
            "cropped": 0,
            "failed": 0,
        }
    }
    temp_dir = tmp_path
    session = Mock()

    with (
        patch("src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping") as mock_download,
        patch("src.main_app.jobs_workers.crop_main_files.process.crop_svg_file") as mock_crop,
        patch("src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename") as mock_generate,
    ):

        mock_download.return_value = {"success": True, "path": tmp_path / "test.svg"}
        mock_crop.return_value = {"success": False, "error": "No footer found"}
        mock_generate.return_value = "File:test (cropped).svg"

        file_info = process.process_one(job_id, template, result, temp_dir, session)

    assert file_info["status"] == "failed"
    assert file_info["reason"] == "crop_failed"
    assert "No footer found" in file_info["error"]
    assert result["summary"]["failed"] == 1
    assert result["summary"]["processed"] == 1


def test_process_one_exception_handling(mock_services, tmp_path):
    """Test handling of exceptions during processing."""
    job_id = 1
    template = TemplateRecord(
        id=1,
        title="Template:Test",
        last_world_file="File:test.svg",
        main_file=None,
    )
    result = {
        "summary": {
            "processed": 0,
            "cropped": 0,
            "failed": 0,
        }
    }
    temp_dir = tmp_path
    session = Mock()

    with patch("src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping") as mock_download:
        mock_download.side_effect = RuntimeError("Unexpected error")

        file_info = process.process_one(job_id, template, result, temp_dir, session)

    assert file_info["status"] == "failed"
    assert file_info["reason"] == "exception"
    assert "RuntimeError" in file_info["error"]
    assert "Unexpected error" in file_info["error"]
    assert result["summary"]["failed"] == 1


def test_process_crops_with_no_templates(mock_services):
    """Test processing when there are no templates."""
    mock_services["list_templates"].return_value = []

    result = {
        "summary": {
            "total": 0,
            "processed": 0,
            "cropped": 0,
            "uploaded": 0,
            "failed": 0,
            "skipped": 0,
        },
        "files_processed": [],
    }

    returned_result = process.process_crops(1, result, "test_result.json", None)

    assert returned_result["summary"]["total"] == 0
    assert returned_result["status"] == "completed"


def test_process_crops_with_templates_no_user(mock_services, tmp_path):
    """Test processing templates without user authentication."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", last_world_file="File:test.svg", main_file=None),
    ]
    mock_services["list_templates"].return_value = templates

    result = {
        "summary": {
            "total": 0,
            "processed": 0,
            "cropped": 0,
            "uploaded": 0,
            "failed": 0,
            "skipped": 0,
        },
        "files_processed": [],
    }

    with (
        patch("src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping") as mock_download,
        patch("src.main_app.jobs_workers.crop_main_files.process.crop_svg_file") as mock_crop,
        patch("src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename") as mock_generate,
    ):

        mock_download.return_value = {"success": True, "path": tmp_path / "test.svg"}
        mock_crop.return_value = {"success": True}
        mock_generate.return_value = "File:test (cropped).svg"

        returned_result = process.process_crops(1, result, "test_result.json", None)

    assert returned_result["summary"]["total"] == 1
    assert returned_result["summary"]["skipped"] == 1
    assert returned_result["summary"]["uploaded"] == 0
    assert returned_result["files_processed"][0]["status"] == "skipped"
    assert returned_result["files_processed"][0]["reason"] == "no_user_auth"


def test_process_crops_with_user_and_upload(mock_services, tmp_path):
    """Test processing templates with user authentication and upload enabled."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", last_world_file="File:test.svg", main_file=None),
    ]
    mock_services["list_templates"].return_value = templates
    user = {"username": "testuser"}

    result = {
        "summary": {
            "total": 0,
            "processed": 0,
            "cropped": 0,
            "uploaded": 0,
            "failed": 0,
            "skipped": 0,
        },
        "files_processed": [],
    }

    with (
        patch("src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping") as mock_download,
        patch("src.main_app.jobs_workers.crop_main_files.process.crop_svg_file") as mock_crop,
        patch("src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename") as mock_generate,
        patch("src.main_app.jobs_workers.crop_main_files.process.upload_one") as mock_upload_one,
    ):

        mock_download.return_value = {"success": True, "path": tmp_path / "test.svg"}
        mock_crop.return_value = {"success": True}
        mock_generate.return_value = "File:test (cropped).svg"

        def upload_one_impl(job_id, file_info, user, result):
            file_info["status"] = "uploaded"
            result["summary"]["uploaded"] += 1

        mock_upload_one.side_effect = upload_one_impl

        returned_result = process.process_crops(1, result, "test_result.json", user, upload_files=True)

    assert returned_result["summary"]["total"] == 1
    assert returned_result["summary"]["uploaded"] == 1
    assert returned_result["summary"]["skipped"] == 0
    assert returned_result["files_processed"][0]["status"] == "uploaded"


def test_process_crops_respects_dev_limit(mock_services, tmp_path):
    """Test that development limit is respected."""
    templates = [
        TemplateRecord(id=i, title=f"Template:Test{i}", last_world_file=f"File:test{i}.svg", main_file=None)
        for i in range(1, 21)
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["settings"].download.dev_limit = 5

    result = {
        "summary": {
            "total": 0,
            "processed": 0,
            "cropped": 0,
            "uploaded": 0,
            "failed": 0,
            "skipped": 0,
        },
        "files_processed": [],
    }

    with (
        patch("src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping") as mock_download,
        patch("src.main_app.jobs_workers.crop_main_files.process.crop_svg_file") as mock_crop,
        patch("src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename") as mock_generate,
    ):

        mock_download.return_value = {"success": True, "path": tmp_path / "test.svg"}
        mock_crop.return_value = {"success": True}
        mock_generate.return_value = "File:test (cropped).svg"

        returned_result = process.process_crops(1, result, "test_result.json", None)

    # Should only process 5 templates due to dev_limit
    assert returned_result["summary"]["total"] == 5


def test_process_crops_respects_cancellation(mock_services):
    """Test that processing respects cancellation event."""
    templates = [
        TemplateRecord(id=i, title=f"Template:Test{i}", last_world_file=f"File:test{i}.svg", main_file=None)
        for i in range(1, 21)
    ]
    mock_services["list_templates"].return_value = templates

    cancel_event = threading.Event()
    cancel_event.set()  # Cancel immediately

    result = {
        "summary": {
            "total": 0,
            "processed": 0,
            "cropped": 0,
            "uploaded": 0,
            "failed": 0,
            "skipped": 0,
        },
        "files_processed": [],
    }

    returned_result = process.process_crops(1, result, "test_result.json", None, cancel_event=cancel_event)

    assert returned_result["status"] == "cancelled"
    assert "cancelled_at" in returned_result


def test_process_crops_saves_progress_periodically(mock_services, tmp_path):
    """Test that progress is saved periodically during processing."""
    templates = [
        TemplateRecord(id=i, title=f"Template:Test{i}", last_world_file=f"File:test{i}.svg", main_file=None)
        for i in range(1, 15)
    ]
    mock_services["list_templates"].return_value = templates

    result = {
        "summary": {
            "total": 0,
            "processed": 0,
            "cropped": 0,
            "uploaded": 0,
            "failed": 0,
            "skipped": 0,
        },
        "files_processed": [],
    }

    with (
        patch("src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping") as mock_download,
        patch("src.main_app.jobs_workers.crop_main_files.process.crop_svg_file") as mock_crop,
        patch("src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename") as mock_generate,
    ):

        mock_download.return_value = {"success": True, "path": tmp_path / "test.svg"}
        mock_crop.return_value = {"success": True}
        mock_generate.return_value = "File:test (cropped).svg"

        process.process_crops(1, result, "test_result.json", None)

    # Should save progress at least twice (at n=1 and n=10)
    assert mock_services["save_job_result_by_name"].call_count >= 2


def test_process_crops_handles_job_not_found(mock_services):
    """Test that process_crops handles job not found gracefully."""
    mock_services["update_job_status"].side_effect = LookupError("Job not found")

    result = {
        "summary": {
            "total": 0,
            "processed": 0,
            "cropped": 0,
            "uploaded": 0,
            "failed": 0,
            "skipped": 0,
        },
        "files_processed": [],
    }

    returned_result = process.process_crops(1, result, "test_result.json", None)

    # Should return the result without crashing
    assert returned_result == result


def test_process_crops_filters_templates_without_main_file(mock_services):
    """Test that templates without main_file are filtered out."""
    templates = [
        TemplateRecord(id=1, title="Template:Test1", last_world_file="File:test1.svg", main_file=None),
        TemplateRecord(id=2, title="Template:Test2", last_world_file=None, main_file=None),
        TemplateRecord(id=3, title="Template:Test3", last_world_file="", main_file=None),
    ]
    mock_services["list_templates"].return_value = templates

    result = {
        "summary": {
            "total": 0,
            "processed": 0,
            "cropped": 0,
            "uploaded": 0,
            "failed": 0,
            "skipped": 0,
        },
        "files_processed": [],
    }

    with (
        patch("src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping") as mock_download,
        patch("src.main_app.jobs_workers.crop_main_files.process.crop_svg_file") as mock_crop,
        patch("src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename") as mock_generate,
    ):

        mock_download.return_value = {"success": True, "path": Path("/tmp/test.svg")}
        mock_crop.return_value = {"success": True}
        mock_generate.return_value = "File:test (cropped).svg"

        returned_result = process.process_crops(1, result, "test_result.json", None)

    # Should only process 1 template (the one with main_file)
    assert returned_result["summary"]["total"] == 1


def test_process_crops_mixed_success_and_failure(mock_services, tmp_path):
    """Test processing with mixed success and failure results."""
    templates = [
        TemplateRecord(id=1, title="Template:Test1", last_world_file="File:test1.svg", main_file=None),
        TemplateRecord(id=2, title="Template:Test2", last_world_file="File:test2.svg", main_file=None),
        TemplateRecord(id=3, title="Template:Test3", last_world_file="File:test3.svg", main_file=None),
    ]
    mock_services["list_templates"].return_value = templates

    result = {
        "summary": {
            "total": 0,
            "processed": 0,
            "cropped": 0,
            "uploaded": 0,
            "failed": 0,
            "skipped": 0,
        },
        "files_processed": [],
    }

    def download_side_effect(filename, temp_dir, session):
        if "test2" in filename:
            return {"success": False, "error": "404 Not Found"}
        return {"success": True, "path": tmp_path / filename}

    with (
        patch("src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping") as mock_download,
        patch("src.main_app.jobs_workers.crop_main_files.process.crop_svg_file") as mock_crop,
        patch("src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename") as mock_generate,
    ):

        mock_download.side_effect = download_side_effect
        mock_crop.return_value = {"success": True}
        mock_generate.return_value = "File:test (cropped).svg"

        returned_result = process.process_crops(1, result, "test_result.json", None)

    assert returned_result["summary"]["total"] == 3
    assert returned_result["summary"]["processed"] == 2  # test1 and test3 downloaded
    assert returned_result["summary"]["failed"] == 1  # test2 failed
    assert len(returned_result["files_processed"]) == 3


def test_process_one_creates_output_path_with_cropped_suffix(mock_services, tmp_path):
    """Test that output path has cropped filename without File: prefix."""
    job_id = 1
    template = TemplateRecord(
        id=1,
        title="Template:Test",
        last_world_file="File:example.svg",
        main_file=None,
    )
    result = {
        "summary": {
            "processed": 0,
            "cropped": 0,
            "failed": 0,
        }
    }
    temp_dir = tmp_path
    session = Mock()

    downloaded_path = tmp_path / "example.svg"

    with (
        patch("src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping") as mock_download,
        patch("src.main_app.jobs_workers.crop_main_files.process.crop_svg_file") as mock_crop,
        patch("src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename") as mock_generate,
    ):

        mock_download.return_value = {"success": True, "path": downloaded_path}
        mock_crop.return_value = {"success": True}
        mock_generate.return_value = "File:example (cropped).svg"

        file_info = process.process_one(job_id, template, result, temp_dir, session)

        # Verify crop was called with correct output path
        crop_call_args = mock_crop.call_args[0]
        assert crop_call_args[0] == downloaded_path
        # Output path should be in temp_dir and not have File: prefix
        expected_output = temp_dir / "example (cropped).svg"
        assert crop_call_args[1] == expected_output


def test_process_crops_updates_job_status_to_running(mock_services):
    """Test that job status is updated to running at start."""
    mock_services["list_templates"].return_value = []

    result = {
        "summary": {
            "total": 0,
            "processed": 0,
            "cropped": 0,
            "uploaded": 0,
            "failed": 0,
            "skipped": 0,
        },
        "files_processed": [],
    }

    process.process_crops(1, result, "test_result.json", None)

    # Verify first call was to set status to running
    first_call = mock_services["update_job_status"].call_args_list[0]
    assert first_call[0][1] == "running"
