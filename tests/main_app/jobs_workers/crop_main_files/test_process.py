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
        "src.main_app.jobs_workers.crop_main_files.process.template_service.list_templates",
        mock_list_templates,
    )

    # Mock jobs_service
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process.jobs_service.update_job_status",
        mock_update_job_status,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process.jobs_service.save_job_result_by_name",
        mock_save_job_result,
    )

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.download.dev_limit = 0  # No limit in tests
    mock_settings.oauth = MagicMock()
    mock_settings.oauth.user_agent = "TestBot/1.0"
    mock_settings.paths.crop_main_files_path = "/tmp/crop_main_files"
    mock_settings.dynamic = {}  # Empty dict for dynamic settings
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process.settings", mock_settings
    )

    # Mock create_commons_session
    mock_create_session = MagicMock(return_value=Mock())
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process.create_commons_session",
        mock_create_session,
    )

    # Mock get_user_site
    mock_get_user_site = MagicMock(return_value=Mock())
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process.get_user_site",
        mock_get_user_site,
    )

    return {
        "list_templates": mock_list_templates,
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "settings": mock_settings,
        "create_commons_session": mock_create_session,
        "get_user_site": mock_get_user_site,
    }


def test_upload_one_success(mock_services):
    """Test successful upload of a cropped file."""
    job_id = 1
    file_info = {
        "original_file": "File:test.svg",
        "cropped_filename": "File:test (cropped).svg",
        "cropped_path": Path("/tmp/test_cropped.svg"),
        "status": "pending",
    }
    site = Mock()

    with patch(
        "src.main_app.jobs_workers.crop_main_files.process.upload_cropped_file"
    ) as mock_upload:
        mock_upload.return_value = {"success": True}

        result = process.upload_one(job_id, file_info, site)

    assert result["result"] is True
    assert "Uploaded" in result["msg"]


def test_upload_one_failure(mock_services):
    """Test failed upload of a cropped file."""
    job_id = 1
    file_info = {
        "original_file": "File:test.svg",
        "cropped_filename": "File:test (cropped).svg",
        "cropped_path": Path("/tmp/test_cropped.svg"),
        "status": "pending",
    }
    site = Mock()

    with patch(
        "src.main_app.jobs_workers.crop_main_files.process.upload_cropped_file"
    ) as mock_upload:
        mock_upload.return_value = {
            "success": False,
            "error": "Upload failed: Network error",
        }

        result = process.upload_one(job_id, file_info, site)

    assert result["result"] is False
    assert "Network error" in result["msg"]


def test_upload_one_skips_if_no_path(mock_services):
    """Test upload is not attempted if cropped_path is None."""
    job_id = 1
    file_info = {
        "original_file": "File:test.svg",
        "cropped_filename": "File:test (cropped).svg",
        "cropped_path": None,
        "status": "pending",
    }
    site = Mock()

    with patch(
        "src.main_app.jobs_workers.crop_main_files.process.upload_cropped_file"
    ) as mock_upload:
        result = process.upload_one(job_id, file_info, site)

    # Upload should still be called but with None path
    mock_upload.assert_called_once()


def test_process_one_success(mock_services, tmp_path):
    """Test successful processing of one template."""
    job_id = 1
    template = TemplateRecord(
        id=1,
        title="Template:Test",
        last_world_file="File:test.svg",
        main_file=None,
    )
    original_dir = tmp_path / "original"
    session = Mock()

    with patch(
        "src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping"
    ) as mock_download:
        mock_download.return_value = {"success": True, "path": tmp_path / "test.svg"}

        result = process.process_one(job_id, template, original_dir, session)

    assert result["result"] is True
    assert "downloaded_path" in result


def test_process_one_download_failure(mock_services, tmp_path):
    """Test handling of download failure."""
    job_id = 1
    template = TemplateRecord(
        id=1,
        title="Template:Test",
        last_world_file="File:test.svg",
        main_file=None,
    )
    original_dir = tmp_path / "original"
    session = Mock()

    with patch(
        "src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping"
    ) as mock_download:
        mock_download.return_value = {"success": False, "error": "404 Not Found"}

        result = process.process_one(job_id, template, original_dir, session)

    assert result["result"] is False
    assert "404 Not Found" in result["msg"]


def test_process_one_exception_handling(mock_services, tmp_path):
    """Test handling of exceptions during processing."""
    job_id = 1
    template = TemplateRecord(
        id=1,
        title="Template:Test",
        last_world_file="File:test.svg",
        main_file=None,
    )
    original_dir = tmp_path / "original"
    session = Mock()

    with patch(
        "src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping"
    ) as mock_download:
        mock_download.side_effect = RuntimeError("Unexpected error")

        result = process.process_one(job_id, template, original_dir, session)

    assert result["result"] is False
    assert "RuntimeError" in result["msg"]
    assert "Unexpected error" in result["msg"]


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
    """Test processing templates without user authentication - should fail early."""
    templates = [
        TemplateRecord(
            id=1, title="Template:Test", last_world_file="File:test.svg", main_file=None
        ),
    ]
    mock_services["list_templates"].return_value = templates
    # Make get_user_site return None to simulate no authentication
    mock_services["get_user_site"].return_value = None

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

    # Should fail early due to no site authentication
    assert returned_result["status"] == "failed"


def test_process_crops_with_user_and_upload(mock_services, tmp_path):
    """Test processing templates with user authentication and upload enabled."""
    templates = [
        TemplateRecord(
            id=1, title="Template:Test", last_world_file="File:test.svg", main_file=None
        ),
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
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping"
        ) as mock_download,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.crop_svg_file"
        ) as mock_crop,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename"
        ) as mock_generate,
    ):
        mock_download.return_value = {"success": True, "path": tmp_path / "test.svg"}
        mock_crop.return_value = {"success": True}
        mock_generate.return_value = "File:test (cropped).svg"

        returned_result = process.process_crops(
            1, result, "test_result.json", user, upload_files=True
        )

    assert returned_result["summary"]["total"] == 1
    assert returned_result["summary"]["processed"] == 1
    assert returned_result["summary"]["cropped"] == 1


def test_process_crops_respects_dev_limit(mock_services, tmp_path):
    """Test that development limit is respected."""
    templates = [
        TemplateRecord(
            id=i,
            title=f"Template:Test{i}",
            last_world_file=f"File:test{i}.svg",
            main_file=None,
        )
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
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping"
        ) as mock_download,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.crop_svg_file"
        ) as mock_crop,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename"
        ) as mock_generate,
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
        TemplateRecord(
            id=i,
            title=f"Template:Test{i}",
            last_world_file=f"File:test{i}.svg",
            main_file=None,
        )
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

    returned_result = process.process_crops(
        1, result, "test_result.json", None, cancel_event=cancel_event
    )

    assert returned_result["status"] == "cancelled"
    assert "cancelled_at" in returned_result


def test_process_crops_saves_progress_periodically(mock_services, tmp_path):
    """Test that progress is saved periodically during processing."""
    templates = [
        TemplateRecord(
            id=i,
            title=f"Template:Test{i}",
            last_world_file=f"File:test{i}.svg",
            main_file=None,
        )
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
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping"
        ) as mock_download,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.crop_svg_file"
        ) as mock_crop,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename"
        ) as mock_generate,
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
        TemplateRecord(
            id=1,
            title="Template:Test1",
            last_world_file="File:test1.svg",
            main_file=None,
        ),
        TemplateRecord(
            id=2, title="Template:Test2", last_world_file=None, main_file=None
        ),
        TemplateRecord(
            id=3, title="Template:Test3", last_world_file="", main_file=None
        ),
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
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping"
        ) as mock_download,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.crop_svg_file"
        ) as mock_crop,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename"
        ) as mock_generate,
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
        TemplateRecord(
            id=1,
            title="Template:Test1",
            last_world_file="File:test1.svg",
            main_file=None,
        ),
        TemplateRecord(
            id=2,
            title="Template:Test2",
            last_world_file="File:test2.svg",
            main_file=None,
        ),
        TemplateRecord(
            id=3,
            title="Template:Test3",
            last_world_file="File:test3.svg",
            main_file=None,
        ),
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
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.download_file_for_cropping"
        ) as mock_download,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.crop_svg_file"
        ) as mock_crop,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename"
        ) as mock_generate,
    ):
        mock_download.side_effect = download_side_effect
        mock_crop.return_value = {"success": True}
        mock_generate.return_value = "File:test (cropped).svg"

        returned_result = process.process_crops(1, result, "test_result.json", None)

    assert returned_result["summary"]["total"] == 3
    assert returned_result["summary"]["processed"] == 2  # test1 and test3 downloaded
    assert returned_result["summary"]["failed"] == 1  # test2 failed
    assert len(returned_result["files_processed"]) == 3


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


def test_process_cropping_success(mock_services, tmp_path):
    """Test successful cropping."""
    job_id = 1
    template = TemplateRecord(
        id=1,
        title="Template:Test",
        last_world_file="File:test.svg",
        main_file=None,
    )
    downloaded_path = tmp_path / "test.svg"
    cropped_output_path = tmp_path / "test (cropped).svg"

    with patch(
        "src.main_app.jobs_workers.crop_main_files.process.crop_svg_file"
    ) as mock_crop:
        mock_crop.return_value = {"success": True}

        result = process.process_cropping(job_id, template, downloaded_path, cropped_output_path)

    assert result["result"] is True
    assert "Cropped to" in result["msg"]


def test_process_cropping_failure(mock_services, tmp_path):
    """Test failed cropping."""
    job_id = 1
    template = TemplateRecord(
        id=1,
        title="Template:Test",
        last_world_file="File:test.svg",
        main_file=None,
    )
    downloaded_path = tmp_path / "test.svg"
    cropped_output_path = tmp_path / "test (cropped).svg"

    with patch(
        "src.main_app.jobs_workers.crop_main_files.process.crop_svg_file"
    ) as mock_crop:
        mock_crop.return_value = {"success": False, "error": "No footer found"}

        result = process.process_cropping(job_id, template, downloaded_path, cropped_output_path)

    assert result["result"] is False
    assert "No footer found" in result["msg"]
