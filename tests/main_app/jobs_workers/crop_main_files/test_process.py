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
    )    # Mock create_commons_session
    mock_create_session = MagicMock(return_value=Mock())
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process.create_commons_session",
        mock_create_session,
    )

    # Mock get_user_site - create a mock site with proper Pages mock
    mock_site = MagicMock()
    mock_page = MagicMock()
    mock_page.exists = False  # Default: cropped file doesn't exist
    mock_site.Pages.__getitem__ = MagicMock(return_value=mock_page)
    mock_get_user_site = MagicMock(return_value=mock_site)
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
        "mock_site": mock_site,
        "mock_page": mock_page,
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
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.get_file_text"
        ) as mock_get_file_text,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.upload_cropped_file"
        ) as mock_upload,
    ):
        mock_download.return_value = {"success": True, "path": tmp_path / "test.svg"}
        mock_crop.return_value = {"success": True}
        mock_generate.return_value = "File:test (cropped).svg"
        mock_get_file_text.return_value = "{{Information}}"
        mock_upload.return_value = {"success": True}

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


# =============================================================================
# Tests for is_cropped_file_existing
# =============================================================================


def test_is_cropped_file_existing_returns_true_when_file_exists(mock_services):
    """Test that is_cropped_file_existing returns True when the cropped file exists."""
    template = TemplateRecord(
        id=1,
        title="Template:Test",
        last_world_file="File:test.svg",
        main_file=None,
    )
    mock_site = Mock()
    mock_page = Mock()
    mock_page.exists = True
    mock_site.Pages.__getitem__ = Mock(return_value=mock_page)

    with patch(
        "src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename"
    ) as mock_generate:
        mock_generate.return_value = "File:test (cropped).svg"

        result = process.is_cropped_file_existing(template, mock_site)

    assert result is True


def test_is_cropped_file_existing_returns_false_when_file_does_not_exist(mock_services):
    """Test that is_cropped_file_existing returns False when the cropped file doesn't exist."""
    template = TemplateRecord(
        id=1,
        title="Template:Test",
        last_world_file="File:test.svg",
        main_file=None,
    )
    mock_site = Mock()
    mock_page = Mock()
    mock_page.exists = False
    mock_site.Pages.__getitem__ = Mock(return_value=mock_page)

    with patch(
        "src.main_app.jobs_workers.crop_main_files.process.generate_cropped_filename"
    ) as mock_generate:
        mock_generate.return_value = "File:test (cropped).svg"

        result = process.is_cropped_file_existing(template, mock_site)

    assert result is False


# =============================================================================
# Tests for update_template_references
# =============================================================================


def test_update_template_references_success(mock_services):
    """Test successful update of template references."""
    job_id = 1
    file_info = {
        "original_file": "File:test.svg",
        "cropped_filename": "File:test (cropped).svg",
        "template_title": "Template:Test",
    }
    mock_site = Mock()

    with (
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.get_page_text"
        ) as mock_get_page,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.update_template_page_file_reference"
        ) as mock_update_ref,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.update_page_text"
        ) as mock_update_page,
    ):
        mock_get_page.return_value = "[[File:test.svg|thumb]]"
        mock_update_ref.return_value = "[[File:test (cropped).svg|thumb]]"
        mock_update_page.return_value = {"success": True}

        result = process.update_template_references(job_id, file_info, mock_site)

    assert result["result"] is True
    assert "Updated template" in result["msg"]


def test_update_template_references_no_update_needed(mock_services):
    """Test when no update is needed for template references."""
    job_id = 1
    file_info = {
        "original_file": "File:test.svg",
        "cropped_filename": "File:test (cropped).svg",
        "template_title": "Template:Test",
    }
    mock_site = Mock()

    with (
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.get_page_text"
        ) as mock_get_page,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.update_template_page_file_reference"
        ) as mock_update_ref,
    ):
        template_text = "No file reference here"
        mock_get_page.return_value = template_text
        # Return unchanged text to indicate no update needed
        mock_update_ref.return_value = template_text

        result = process.update_template_references(job_id, file_info, mock_site)

    assert result["result"] is None
    assert "No update needed" in result["msg"]


def test_update_template_references_failure(mock_services):
    """Test handling of failed template reference update."""
    job_id = 1
    file_info = {
        "original_file": "File:test.svg",
        "cropped_filename": "File:test (cropped).svg",
        "template_title": "Template:Test",
    }
    mock_site = Mock()

    with (
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.get_page_text"
        ) as mock_get_page,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.update_template_page_file_reference"
        ) as mock_update_ref,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.update_page_text"
        ) as mock_update_page,
    ):
        mock_get_page.return_value = "[[File:test.svg|thumb]]"
        mock_update_ref.return_value = "[[File:test (cropped).svg|thumb]]"
        mock_update_page.return_value = {"success": False, "error": "Permission denied"}

        result = process.update_template_references(job_id, file_info, mock_site)

    assert result["result"] is False
    assert "Failed to update template" in result["msg"]


# =============================================================================
# Tests for update_original_file_wikitext
# =============================================================================


def test_update_original_file_wikitext_success(mock_services):
    """Test successful update of original file wikitext."""
    job_id = 1
    file_info = {
        "original_file": "File:test.svg",
        "cropped_filename": "File:test (cropped).svg",
    }
    mock_site = Mock()

    with (
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.get_file_text"
        ) as mock_get_file,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.update_original_file_text"
        ) as mock_update_text,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.update_file_text"
        ) as mock_update_file,
    ):
        mock_get_file.return_value = "{{Information}}"
        mock_update_text.return_value = "{{Information|other_versions={{Image extracted|test.svg}}}}"
        mock_update_file.return_value = {"success": True}

        result = process.update_original_file_wikitext(job_id, file_info, mock_site)

    assert result["result"] is True
    assert "Updated original file wikitext" in result["msg"]


def test_update_original_file_wikitext_no_update_needed(mock_services):
    """Test when no update is needed for original file wikitext."""
    job_id = 1
    file_info = {
        "original_file": "File:test.svg",
        "cropped_filename": "File:test (cropped).svg",
    }
    mock_site = Mock()

    with (
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.get_file_text"
        ) as mock_get_file,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.update_original_file_text"
        ) as mock_update_text,
    ):
        wikitext = "{{Information|other_versions={{Image extracted|test (cropped).svg}}}}"
        mock_get_file.return_value = wikitext
        # Return unchanged text to indicate no update needed
        mock_update_text.return_value = wikitext

        result = process.update_original_file_wikitext(job_id, file_info, mock_site)

    assert result["result"] is None
    assert "No update needed" in result["msg"]


def test_update_original_file_wikitext_failure(mock_services):
    """Test handling of failed original file wikitext update."""
    job_id = 1
    file_info = {
        "original_file": "File:test.svg",
        "cropped_filename": "File:test (cropped).svg",
    }
    mock_site = Mock()

    with (
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.get_file_text"
        ) as mock_get_file,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.update_original_file_text"
        ) as mock_update_text,
        patch(
            "src.main_app.jobs_workers.crop_main_files.process.update_file_text"
        ) as mock_update_file,
    ):
        mock_get_file.return_value = "{{Information}}"
        mock_update_text.return_value = "{{Information|other_versions={{Image extracted|test.svg}}}}"
        mock_update_file.return_value = {"success": False, "error": "Protected page"}

        result = process.update_original_file_wikitext(job_id, file_info, mock_site)

    assert result["result"] is False
    assert "Protected page" in result["msg"]


# =============================================================================
# Tests for upload_one file_exists handling
# =============================================================================


def test_upload_one_file_already_exists(mock_services):
    """Test upload_one skips when file already exists on Commons."""
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
        mock_upload.return_value = {"success": False, "file_exists": True}

        result = process.upload_one(job_id, file_info, site)

    assert result["result"] is None
    assert "already exists" in result["msg"]


# =============================================================================
# Tests for _apply_limits
# =============================================================================


def test_apply_limits_with_upload_limit(mock_services):
    """Test that upload limit from dynamic settings is applied."""
    mock_services["settings"].dynamic = {"crop_newest_upload_limit": 3}
    mock_services["settings"].download.dev_limit = 0  # Disable dev limit

    templates = [
        TemplateRecord(
            id=i,
            title=f"Template:Test{i}",
            last_world_file=f"File:test{i}.svg",
            main_file=None,
        )
        for i in range(1, 11)  # 10 templates
    ]

    result = process._apply_limits(1, templates)

    assert len(result) == 3


def test_apply_limits_without_any_limits(mock_services):
    """Test that no limit is applied when both limits are 0."""
    mock_services["settings"].dynamic = {"crop_newest_upload_limit": 0}
    mock_services["settings"].download.dev_limit = 0

    templates = [
        TemplateRecord(
            id=i,
            title=f"Template:Test{i}",
            last_world_file=f"File:test{i}.svg",
            main_file=None,
        )
        for i in range(1, 11)  # 10 templates
    ]

    result = process._apply_limits(1, templates)

    assert len(result) == 10
