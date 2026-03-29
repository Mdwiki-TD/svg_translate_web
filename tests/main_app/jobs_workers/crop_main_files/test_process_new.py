"""Unit tests for crop_main_files/process_new module."""

from __future__ import annotations

import threading
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.crop_main_files.process_new import (
    CropMainFilesProcessor,
    FileProcessingInfo,
    is_cropped_file_existing,
    process_crops,
)
from src.main_app.template_service import TemplateRecord


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch, mock_jobs_service):
    """Mock the services used by process_new module."""

    # Mock jobs_service
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.jobs_service.update_job_status",
        mock_update_job_status,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.jobs_service.save_job_result_by_name",
        mock_save_job_result,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.jobs_service.is_job_cancelled",
        mock_jobs_service,
    )

    # Mock template_service
    mock_list_templates = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.template_service.list_templates",
        mock_list_templates,
    )

    # Mock API clients
    mock_get_user_site = MagicMock()
    mock_create_commons_session = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.get_user_site",
        mock_get_user_site,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.create_commons_session",
        mock_create_commons_session,
    )

    # Mock text_api functions
    mock_get_file_text = MagicMock()
    mock_get_page_text = MagicMock()
    mock_update_file_text = MagicMock()
    mock_update_page_text = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.get_file_text",
        mock_get_file_text,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.get_page_text",
        mock_get_page_text,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.update_file_text",
        mock_update_file_text,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.update_page_text",
        mock_update_page_text,
    )

    # Mock crop_file functions
    mock_download_file = MagicMock()
    mock_crop_svg_file = MagicMock()
    mock_upload_cropped_file = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.download_file_for_cropping",
        mock_download_file,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.crop_svg_file",
        mock_crop_svg_file,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.upload_cropped_file",
        mock_upload_cropped_file,
    )

    # Mock wikitext utilities
    mock_create_cropped_file_text = MagicMock(return_value="Cropped file wikitext")
    mock_update_original_file_text = MagicMock(return_value="Updated original text")
    mock_update_template_page_file_reference = MagicMock(return_value="Updated template text")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.create_cropped_file_text",
        mock_create_cropped_file_text,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.update_original_file_text",
        mock_update_original_file_text,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.update_template_page_file_reference",
        mock_update_template_page_file_reference,
    )

    # Mock utils
    mock_generate_cropped_filename = MagicMock(side_effect=lambda x: f"File:{x.replace('File:', '')} (cropped).svg")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.generate_cropped_filename",
        mock_generate_cropped_filename,
    )

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.paths.crop_main_files_path = "/tmp/crop_main_files"
    mock_settings.oauth.user_agent = "TestBot/1.0"
    mock_settings.dynamic = {}
    mock_settings.download.dev_limit = 0
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.process_new.settings",
        mock_settings,
    )

    return {
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "list_templates": mock_list_templates,
        "get_user_site": mock_get_user_site,
        "create_commons_session": mock_create_commons_session,
        "get_file_text": mock_get_file_text,
        "get_page_text": mock_get_page_text,
        "update_file_text": mock_update_file_text,
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


class TestFileProcessingInfo:
    """Tests for FileProcessingInfo dataclass."""

    def test_default_initialization(self):
        """Test FileProcessingInfo initializes with correct defaults."""
        info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        assert info.template_id == 1
        assert info.template_title == "Template:Test"
        assert info.original_file == "File:test.svg"
        assert info.cropped_filename == "File:test (cropped).svg"
        assert info.status == "pending"
        assert info.error is None
        assert info.downloaded_path is None
        assert info.cropped_path is None
        assert "download" in info.steps
        assert "crop" in info.steps
        assert "upload_cropped" in info.steps

    def test_to_dict(self):
        """Test to_dict serialization."""
        info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
            status="completed",
            error=None,
            downloaded_path=Path("/tmp/test.svg"),
            cropped_path=Path("/tmp/test_cropped.svg"),
        )
        info.steps["download"] = {"result": True, "msg": "Downloaded"}

        result = info.to_dict()

        assert result["template_id"] == 1
        assert result["template_title"] == "Template:Test"
        assert result["downloaded_path"] == str(Path("/tmp/test.svg"))
        assert result["cropped_path"] == str(Path("/tmp/test_cropped.svg"))
        assert result["status"] == "completed"

    def test_to_dict_with_none_paths(self):
        """Test to_dict with None paths."""
        info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        result = info.to_dict()

        assert result["downloaded_path"] is None
        assert result["cropped_path"] is None


class TestIsCroppedFileExisting:
    """Tests for is_cropped_file_existing function."""

    def test_file_exists(self):
        """Test when cropped file already exists."""
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.exists = True
        mock_site.pages = {"File:test (cropped).svg": mock_page}

        result = is_cropped_file_existing("File:test (cropped).svg", mock_site)

        assert result is True

    def test_file_does_not_exist(self):
        """Test when cropped file does not exist."""
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.exists = False
        mock_site.pages = {"File:test (cropped).svg": mock_page}

        result = is_cropped_file_existing("File:test (cropped).svg", mock_site)

        assert result is False


class TestCropMainFilesProcessorInitialization:
    """Tests for CropMainFilesProcessor initialization."""

    def test_processor_initialization(self, mock_services):
        """Test processor initializes correctly."""
        initial_result = {
            "status": "pending",
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

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user={"username": "test"},
            upload_files=True,
        )

        assert processor.job_id == 1
        assert processor.result_file == "test_result.json"
        assert processor.user == {"username": "test"}
        assert processor.upload_files is True
        assert processor.site is None
        assert processor.session is None

    def test_processor_default_upload_files(self, mock_services):
        """Test processor defaults upload_files to False."""
        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        assert processor.upload_files is False


class TestCropMainFilesProcessorBeforeRun:
    """Tests for before_run method."""

    def test_before_run_success(self, mock_services):
        """Test before_run with successful initialization."""
        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user={"username": "test"},
        )

        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["create_commons_session"].return_value = MagicMock()

        result = processor.before_run()

        assert result is True
        assert processor.site is not None
        assert processor.session is not None
        mock_services["update_job_status"].assert_called_once_with(
            1, "running", "test_result.json", job_type="crop_main_files"
        )

    def test_before_run_lookup_error(self, mock_services):
        """Test before_run when job record not found."""
        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user={"username": "test"},
        )

        mock_services["update_job_status"].side_effect = LookupError("Job not found")

        result = processor.before_run()

        assert result is False

    def test_before_run_no_site_auth(self, mock_services):
        """Test before_run when site authentication fails."""
        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        mock_services["get_user_site"].return_value = None
        mock_services["create_commons_session"].return_value = MagicMock()

        result = processor.before_run()

        assert result is False
        assert initial_result["status"] == "failed"
        assert "failed_at" in initial_result


class TestCropMainFilesProcessorLoadTemplates:
    """Tests for _load_templates and _apply_limits."""

    def test_load_templates_filters_by_last_world_file(self, mock_services):
        """Test that only templates with last_world_file are loaded."""
        templates = [
            TemplateRecord(id=1, title="Template:Test1", main_file="test1.svg", last_world_file="test1_2020.svg"),
            TemplateRecord(id=2, title="Template:Test2", main_file="test2.svg", last_world_file=None),
            TemplateRecord(id=3, title="Template:Test3", main_file="test3.svg", last_world_file="test3_2020.svg"),
        ]
        mock_services["list_templates"].return_value = templates

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        result = processor._load_templates()

        assert len(result) == 2
        assert all(t.last_world_file is not None for t in result)

    def test_apply_limits_with_crop_newest_upload_limit(self, mock_services):
        """Test _apply_limits respects crop_newest_upload_limit setting."""
        mock_services["settings"].dynamic = {"crop_newest_upload_limit": 2}
        templates = [
            TemplateRecord(id=1, title="Template:Test1", main_file="test1.svg", last_world_file="test1_2020.svg"),
            TemplateRecord(id=2, title="Template:Test2", main_file="test2.svg", last_world_file="test2_2020.svg"),
            TemplateRecord(id=3, title="Template:Test3", main_file="test3.svg", last_world_file="test3_2020.svg"),
        ]

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        result = processor._apply_limits(templates)

        assert len(result) == 2

    def test_apply_limits_with_dev_limit(self, mock_services):
        """Test _apply_limits respects dev_limit setting."""
        mock_services["settings"].download.dev_limit = 2
        templates = [
            TemplateRecord(id=1, title="Template:Test1", main_file="test1.svg", last_world_file="test1_2020.svg"),
            TemplateRecord(id=2, title="Template:Test2", main_file="test2.svg", last_world_file="test2_2020.svg"),
            TemplateRecord(id=3, title="Template:Test3", main_file="test3.svg", last_world_file="test3_2020.svg"),
        ]

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        result = processor._apply_limits(templates)

        assert len(result) == 2


class TestCropMainFilesProcessorSteps:
    """Tests for individual pipeline steps."""

    def test_step_download_success(self, mock_services, tmp_path):
        """Test _step_download with successful download."""
        mock_services["download_file"].return_value = {"success": True, "path": str(tmp_path / "test.svg")}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )
        template = TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file="test_2020.svg")

        result = processor._step_download(file_info, template)

        assert result is True
        assert str(file_info.downloaded_path) == str(tmp_path / "test.svg")
        assert file_info.steps["download"]["result"] is True
        assert initial_result["summary"]["processed"] == 1

    def test_step_download_failure(self, mock_services):
        """Test _step_download when download fails."""
        mock_services["download_file"].return_value = {"success": False, "error": "Network error"}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )
        template = TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file="test_2020.svg")

        result = processor._step_download(file_info, template)

        assert result is False
        assert file_info.status == "failed"
        assert file_info.steps["download"]["result"] is False
        assert "Network error" in file_info.steps["download"]["msg"]
        assert initial_result["summary"]["failed"] == 1

    def test_step_download_exception(self, mock_services):
        """Test _step_download when exception occurs."""
        mock_services["download_file"].side_effect = ConnectionError("Connection refused")

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )
        template = TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file="test_2020.svg")

        result = processor._step_download(file_info, template)

        assert result is False
        assert file_info.status == "failed"
        assert "ConnectionError" in file_info.steps["download"]["msg"]

    def test_step_crop_success(self, mock_services, tmp_path):
        """Test _step_crop with successful crop."""
        mock_services["crop_svg_file"].return_value = {"success": True}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )
        file_info.downloaded_path = tmp_path / "test.svg"
        template = TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file="test_2020.svg")
        cropped_output_path = tmp_path / "test (cropped).svg"

        result = processor._step_crop(file_info, template, cropped_output_path)

        assert result is True
        assert file_info.cropped_path == cropped_output_path
        assert file_info.steps["crop"]["result"] is True
        assert initial_result["summary"]["cropped"] == 1

    def test_step_crop_failure(self, mock_services, tmp_path):
        """Test _step_crop when crop fails."""
        mock_services["crop_svg_file"].return_value = {"success": False, "error": "Invalid SVG"}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )
        file_info.downloaded_path = tmp_path / "test.svg"
        template = TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file="test_2020.svg")
        cropped_output_path = tmp_path / "test (cropped).svg"

        result = processor._step_crop(file_info, template, cropped_output_path)

        assert result is False
        assert file_info.status == "failed"
        assert file_info.steps["crop"]["result"] is False
        assert "Invalid SVG" in file_info.steps["crop"]["msg"]
        assert initial_result["summary"]["failed"] == 1

    def test_step_upload_success(self, mock_services, tmp_path):
        """Test _step_upload with successful upload."""
        mock_services["get_file_text"].return_value = "Original file text"
        mock_services["upload_cropped_file"].return_value = {"success": True}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )
        processor.site = MagicMock()

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )
        file_info.cropped_path = tmp_path / "test (cropped).svg"

        result = processor._step_upload(file_info)

        assert result is True
        assert file_info.status == "uploaded"
        assert file_info.steps["upload_cropped"]["result"] is True
        assert initial_result["summary"]["uploaded"] == 1

    def test_step_upload_file_exists(self, mock_services, tmp_path):
        """Test _step_upload when file already exists."""
        mock_services["get_file_text"].return_value = "Original file text"
        mock_services["upload_cropped_file"].return_value = {"success": False, "file_exists": True}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )
        processor.site = MagicMock()

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )
        file_info.cropped_path = tmp_path / "test (cropped).svg"

        result = processor._step_upload(file_info)

        assert result is True  # Should continue to wikitext updates
        assert file_info.status == "skipped"
        assert initial_result["summary"]["skipped"] == 1

    def test_step_upload_failure(self, mock_services, tmp_path):
        """Test _step_upload when upload fails."""
        mock_services["get_file_text"].return_value = "Original file text"
        mock_services["upload_cropped_file"].return_value = {"success": False, "error": "Upload failed"}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )
        processor.site = MagicMock()

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )
        file_info.cropped_path = tmp_path / "test (cropped).svg"

        result = processor._step_upload(file_info)

        assert result is False
        assert file_info.status == "failed"
        assert file_info.error == "Upload failed"
        assert initial_result["summary"]["failed"] == 1

    def test_step_update_original_no_change(self, mock_services):
        """Test _step_update_original when no update is needed."""
        mock_services["get_file_text"].return_value = "Original file text"
        mock_services["update_original_file_text"].return_value = "Original file text"  # No change

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )
        processor.site = MagicMock()

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._step_update_original(file_info)

        assert file_info.steps["update_original"]["result"] is None
        assert file_info.steps["update_original"]["msg"] == "No update needed"
        mock_services["update_file_text"].assert_not_called()

    def test_step_update_original_with_update(self, mock_services):
        """Test _step_update_original when update is performed."""
        mock_services["get_file_text"].return_value = "Original file text"
        mock_services["update_original_file_text"].return_value = "Updated file text"
        mock_services["update_file_text"].return_value = {"success": True}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )
        processor.site = MagicMock()

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._step_update_original(file_info)

        assert file_info.steps["update_original"]["result"] is True
        mock_services["update_file_text"].assert_called_once()

    def test_step_update_original_update_fails(self, mock_services):
        """Test _step_update_original when update fails."""
        mock_services["get_file_text"].return_value = "Original file text"
        mock_services["update_original_file_text"].return_value = "Updated file text"
        mock_services["update_file_text"].return_value = {"success": False, "error": "Edit conflict"}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )
        processor.site = MagicMock()

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._step_update_original(file_info)

        assert file_info.steps["update_original"]["result"] is False
        assert "Edit conflict" in file_info.steps["update_original"]["msg"]

    def test_step_update_template_no_change(self, mock_services):
        """Test _step_update_template when no update is needed."""
        mock_services["get_page_text"].return_value = "Template text"
        mock_services["update_template_page_file_reference"].return_value = "Template text"  # No change

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )
        processor.site = MagicMock()

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._step_update_template(file_info)

        assert file_info.steps["update_template"]["result"] is None
        assert file_info.steps["update_template"]["msg"] == "No update needed"
        mock_services["update_page_text"].assert_not_called()

    def test_step_update_template_with_update(self, mock_services):
        """Test _step_update_template when update is performed."""
        mock_services["get_page_text"].return_value = "Template text"
        mock_services["update_template_page_file_reference"].return_value = "Updated template text"
        mock_services["update_page_text"].return_value = {"success": True}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )
        processor.site = MagicMock()

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._step_update_template(file_info)

        assert file_info.steps["update_template"]["result"] is True
        mock_services["update_page_text"].assert_called_once()


class TestCropMainFilesProcessorHelpers:
    """Tests for helper methods."""

    def test_fail_updates_status_and_result(self, mock_services):
        """Test _fail updates info status and result summary."""
        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._fail(file_info, "download", "Download failed")

        assert file_info.status == "failed"
        assert file_info.error == "Download failed"
        assert file_info.steps["download"]["result"] is False
        assert initial_result["summary"]["failed"] == 1

    def test_skip_step_updates_step_status(self, mock_services):
        """Test _skip_step updates step status."""
        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._skip_step(file_info, "upload_cropped", "Already exists")

        assert file_info.steps["upload_cropped"]["result"] is None
        assert file_info.steps["upload_cropped"]["msg"] == "Already exists"

    def test_skip_upload_steps(self, mock_services):
        """Test _skip_upload_steps marks upload steps as skipped."""
        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._skip_upload_steps(file_info)

        assert file_info.status == "skipped"
        assert file_info.steps["upload_cropped"]["result"] is None
        assert file_info.steps["update_original"]["result"] is None
        assert file_info.steps["update_template"]["result"] is None
        assert initial_result["summary"]["skipped"] == 1
        assert file_info.cropped_filename is None

    def test_is_cancelled_with_event(self, mock_services):
        """Test _is_cancelled with cancel event."""
        cancel_event = threading.Event()

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
            cancel_event=cancel_event,
        )

        assert processor._is_cancelled() is False

        cancel_event.set()
        assert processor._is_cancelled() is True
        assert initial_result["status"] == "cancelled"

    def test_is_cancelled_with_global_check(self, mock_services):
        """Test _is_cancelled with global job cancellation check."""
        mock_services["is_job_cancelled"].return_value = True

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        assert processor._is_cancelled() is True
        assert initial_result["status"] == "cancelled"

    def test_append_adds_to_result(self, mock_services):
        """Test _append adds info to files_processed list."""
        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        file_info = FileProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._append(file_info)

        assert len(initial_result["files_processed"]) == 1
        assert initial_result["files_processed"][0]["template_id"] == 1

    def test_get_priority(self, mock_services):
        """Test get_priority calculates correct interval."""
        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        assert processor.get_priority(5) == 1
        assert processor.get_priority(10) == 1
        assert processor.get_priority(25) == 2
        assert processor.get_priority(100) == 10
        assert processor.get_priority(200) == 10


class TestCropMainFilesProcessorProcessTemplate:
    """Tests for _process_template method."""

    def test_process_template_file_already_exists(self, mock_services):
        """Test processing when cropped file already exists on Commons."""
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.exists = True
        # Use a MagicMock for Pages to handle any key access
        mock_pages = MagicMock()
        mock_pages.__getitem__ = MagicMock(return_value=mock_page)
        mock_site.pages = mock_pages

        mock_services["get_user_site"].return_value = mock_site
        mock_services["get_file_text"].return_value = "Original file text"
        mock_services["update_original_file_text"].return_value = "Updated original"
        mock_services["update_file_text"].return_value = {"success": True}
        mock_services["get_page_text"].return_value = "Template text"
        mock_services["update_template_page_file_reference"].return_value = "Updated template"
        mock_services["update_page_text"].return_value = {"success": True}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
            upload_files=True,
        )
        processor.site = mock_site

        template = TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file="test_2020.svg")

        processor._process_template(template)

        # Should skip download, crop, and upload steps
        assert initial_result["files_processed"][0]["steps"]["download"]["result"] is None
        assert "Skipped" in initial_result["files_processed"][0]["steps"]["download"]["msg"]

    def test_process_template_full_pipeline(self, mock_services, tmp_path):
        """Test full pipeline for a new file."""
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.exists = False
        # Use a MagicMock for Pages to handle any key access
        mock_pages = MagicMock()
        mock_pages.__getitem__ = MagicMock(return_value=mock_page)
        mock_site.pages = mock_pages

        mock_services["get_user_site"].return_value = mock_site
        mock_services["download_file"].return_value = {"success": True, "path": str(tmp_path / "test.svg")}
        mock_services["crop_svg_file"].return_value = {"success": True}
        mock_services["get_file_text"].return_value = "Original file text"
        mock_services["upload_cropped_file"].return_value = {"success": True}
        mock_services["update_original_file_text"].return_value = "Updated original"
        mock_services["update_file_text"].return_value = {"success": True}
        mock_services["get_page_text"].return_value = "Template text"
        mock_services["update_template_page_file_reference"].return_value = "Updated template"
        mock_services["update_page_text"].return_value = {"success": True}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
            upload_files=True,
        )
        processor.site = mock_site
        processor.original_dir = tmp_path / "original"
        processor.cropped_dir = tmp_path / "cropped"

        template = TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file="test_2020.svg")

        processor._process_template(template)

        file_result = initial_result["files_processed"][0]
        assert file_result["steps"]["download"]["result"] is True
        assert file_result["steps"]["crop"]["result"] is True
        assert file_result["steps"]["upload_cropped"]["result"] is True

    def test_process_template_upload_disabled(self, mock_services, tmp_path):
        """Test processing when upload_files is False."""
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.exists = False
        # Use a MagicMock for Pages to handle any key access
        mock_pages = MagicMock()
        mock_pages.__getitem__ = MagicMock(return_value=mock_page)
        mock_site.pages = mock_pages

        mock_services["download_file"].return_value = {"success": True, "path": str(tmp_path / "test.svg")}
        mock_services["crop_svg_file"].return_value = {"success": True}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
            upload_files=False,
        )
        processor.site = mock_site
        processor.original_dir = tmp_path / "original"
        processor.cropped_dir = tmp_path / "cropped"

        template = TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file="test_2020.svg")

        processor._process_template(template)

        # Should skip upload steps
        assert initial_result["files_processed"][0]["steps"]["upload_cropped"]["result"] is None
        assert "upload disabled" in initial_result["files_processed"][0]["steps"]["upload_cropped"]["msg"].lower()
        assert initial_result["summary"]["skipped"] == 1


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
        mock_services["get_file_text"].return_value = "Original file text"
        mock_services["upload_cropped_file"].return_value = {"success": True}
        mock_services["update_original_file_text"].return_value = "Updated original"
        mock_services["update_file_text"].return_value = {"success": True}
        mock_services["get_page_text"].return_value = "Template text"
        mock_services["update_template_page_file_reference"].return_value = "Updated template"
        mock_services["update_page_text"].return_value = {"success": True}

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
            upload_files=True,
        )

        result = processor.run()

        assert result["status"] == "completed"
        assert result["summary"]["total"] == 1
        assert result["summary"]["processed"] == 1
        assert result["summary"]["cropped"] == 1
        assert result["summary"]["uploaded"] == 1

    def test_run_before_run_fails(self, mock_services):
        """Test run when before_run returns False."""
        mock_services["update_job_status"].side_effect = LookupError("Job not found")

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        processor = CropMainFilesProcessor(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
        )

        result = processor.run()

        # Should return early with original result
        assert result["status"] == "pending"


class TestProcessCrops:
    """Tests for process_crops entry point."""

    def test_entry_point_creates_processor_and_runs(self, mock_services, tmp_path):
        """Test that process_crops creates processor and runs it."""
        mock_site = MagicMock()
        mock_page = MagicMock()
        mock_page.exists = False
        mock_site.pages = {"File:test (cropped).svg": mock_page}

        mock_services["get_user_site"].return_value = mock_site
        mock_services["create_commons_session"].return_value = MagicMock()
        mock_services["list_templates"].return_value = []

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        result = process_crops(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
            cancel_event=None,
            upload_files=False,
        )

        assert result["status"] == "completed"

    def test_entry_point_with_cancel_event(self, mock_services):
        """Test process_crops with cancel event."""
        cancel_event = threading.Event()

        mock_services["update_job_status"].side_effect = LookupError("Job not found")

        initial_result = {
            "status": "pending",
            "summary": {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0},
            "files_processed": [],
        }

        result = process_crops(
            job_id=1,
            result=initial_result,
            result_file="test_result.json",
            user=None,
            cancel_event=cancel_event,
            upload_files=False,
        )

        assert result["status"] == "pending"  # before_run failed
