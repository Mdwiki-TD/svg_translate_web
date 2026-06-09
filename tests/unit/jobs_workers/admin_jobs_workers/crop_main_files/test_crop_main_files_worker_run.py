"""Unit tests for crop_main_files/worker module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker import CropMainFilesWorker


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch, mock_jobs_service):
    """Mock the services used by worker module."""

    # Mock jobs_service
    mock_save_job_result = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name",
        mock_save_job_result,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.is_job_cancelled",
        mock_jobs_service,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.update_job_status",
        MagicMock(),
    )

    # Mock list_templates
    mock_list_templates = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.list_templates",
        mock_list_templates,
    )

    # Mock API clients
    mock_get_user_site = MagicMock()
    mock_create_commons_session = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.get_user_site",
        mock_get_user_site,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.create_commons_session",
        mock_create_commons_session,
    )

    # Mock pages_api functions
    mock_get_page_text = MagicMock()
    mock_update_page_text = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.get_page_text",
        mock_get_page_text,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.update_page_text",
        mock_update_page_text,
    )

    # Mock query_api functions
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.is_pages_exists",
        MagicMock(return_value={}),
    )

    # Mock crop_file functions
    mock_download_file = MagicMock()
    mock_crop_svg_file = MagicMock()
    mock_upload_cropped_file = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.download_file_for_cropping",
        mock_download_file,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.crop_svg_file",
        mock_crop_svg_file,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.upload_cropped_file",
        mock_upload_cropped_file,
    )

    # Mock wikitext utilities
    mock_create_cropped_file_text = MagicMock(return_value="Cropped file wikitext")
    mock_update_original_file_text = MagicMock(return_value="Updated original text")
    mock_update_template_page_file_reference = MagicMock(return_value="Updated template text")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.create_cropped_file_text",
        mock_create_cropped_file_text,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.update_original_file_text",
        mock_update_original_file_text,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.update_template_page_file_reference",
        mock_update_template_page_file_reference,
    )

    # Mock utils
    mock_generate_cropped_filename = MagicMock(side_effect=lambda x: f"File:{x.replace('File:', '')} (cropped).svg")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.generate_cropped_filename",
        mock_generate_cropped_filename,
    )

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.paths.crop_main_files_path = "/tmp/crop_main_files"
    mock_settings.other.user_agent = "TestBot/1.0"
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.settings",
        mock_settings,
    )

    return {
        "save_job_result_by_name": mock_save_job_result,
        "list_templates": mock_list_templates,
        "get_user_site": mock_get_user_site,
        "create_commons_session": mock_create_commons_session,
        "get_page_text": mock_get_page_text,
        "update_page_text": mock_update_page_text,
        "download_file": mock_download_file,
        "crop_svg_file": mock_crop_svg_file,
        "upload_cropped_file": mock_upload_cropped_file,
        "create_cropped_file_text": mock_create_cropped_file_text,
        "update_original_file_text": mock_update_original_file_text,
        "update_template_page_file_reference": mock_update_template_page_file_reference,
        "generate_cropped_filename": mock_generate_cropped_filename,
        "settings": mock_settings,
        "is_job_cancelled": mock_jobs_service,
    }


class TestCropMainFilesProcessorRun:
    """Tests for run method."""

    def test_run_full_workflow(self, mock_services, tmp_path):
        """Test complete run workflow."""
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.exists = False
        # Use a MagicMock for Pages to handle any key access
        mock_pages = MagicMock()
        mock_pages.__getitem__ = MagicMock(return_value=mock_page)
        mock_site.pages = mock_pages

        mock_services["get_user_site"].return_value = mock_site
        mock_services["create_commons_session"].return_value = MagicMock()
        mock_services["list_templates"].return_value = [
            TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file="test_2020.svg"),
        ]
        mock_services["download_file"].return_value = {"success": True, "path": str(tmp_path / "test.svg")}
        mock_services["crop_svg_file"].return_value = {"success": True}
        mock_services["upload_cropped_file"].return_value = {"success": True}
        mock_services["update_original_file_text"].return_value = "Updated original"
        mock_services["get_page_text"].return_value = "Template text"
        mock_services["update_template_page_file_reference"].return_value = "Updated template"
        mock_services["update_page_text"].return_value = {"success": True}

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
            args={"upload_files": True},
        )

        result = processor.run()

        assert result["status"] == "completed"
        assert result["summary"]["total"] == 1
        assert result["summary"]["processed"] == 1
        assert result["summary"]["cropped"] == 1
        assert result["summary"]["uploaded"] == 1

    def test_run_before_run_fails(self, monkeypatch):
        """Test run when before_run returns False."""
        mock_update_job_status = MagicMock()
        monkeypatch.setattr(
            "src.main_app.jobs_workers.base_worker.update_job_status",
            mock_update_job_status,
        )
        mock_update_job_status.side_effect = LookupError("Job not found")

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        result = processor.run()

        # Should return early with original result
        assert result["status"] == "completed"
