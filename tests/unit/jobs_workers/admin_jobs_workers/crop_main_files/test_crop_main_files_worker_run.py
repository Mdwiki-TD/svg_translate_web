"""Unit tests for crop_main_files/worker module."""

from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker import (
    CropMainFilesWorker,
    TemplateProcessingInfo,
)


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch, mock_jobs_service):
    """Mock the services used by worker module."""

    # Mock jobs_service
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.update_job_status",
        mock_update_job_status,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name",
        mock_save_job_result,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.is_job_cancelled",
        mock_jobs_service,
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

    # Mock pages_api / MwClientPage
    mock_mwclientpage = MagicMock()
    mock_mwclientpage.return_value.exists.return_value = False
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.MwClientPage",
        mock_mwclientpage,
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
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "list_templates": mock_list_templates,
        "get_user_site": mock_get_user_site,
        "create_commons_session": mock_create_commons_session,
        "MwClientPage": mock_mwclientpage,
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
    """Tests for TemplateInfo dataclass."""

    def test_default_initialization(self):
        """Test TemplateInfo initializes with correct defaults."""
        info = TemplateProcessingInfo(
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
        info = TemplateProcessingInfo(
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
        info = TemplateProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        result = info.to_dict()

        assert result["downloaded_path"] is None
        assert result["cropped_path"] is None


class TestCropMainFilesProcessorInitialization:
    """Tests for CropMainFilesWorker initialization."""

    def test_processor_initialization(self, mock_services):
        """Test processor initializes correctly."""
        processor = CropMainFilesWorker(
            job_id=1,
            user={"username": "test"},
            args={"upload_files": True},
        )

        assert processor.job_id == 1
        assert processor.result_file == "crop_main_files_job_1.json"
        assert processor.user == {"username": "test"}
        assert processor.upload_files is True
        assert processor.site is None

    def test_processor_default_upload_files(self, mock_services):
        """Test processor defaults upload_files to False."""

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        assert processor.upload_files is False


class TestCropMainFilesProcessorBeforeRun:
    """Tests for before_run method."""

    def test_before_run_success(self, mock_services):
        """Test before_run with successful initialization."""

        processor = CropMainFilesWorker(
            job_id=1,
            user={"username": "test"},
        )

        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["create_commons_session"].return_value = MagicMock()

        result = processor.before_run()

        assert result is True
        mock_services["update_job_status"].assert_called_once_with(
            1, "running", "crop_main_files_job_1.json", job_type="crop_main_files"
        )

    def test_before_run_lookup_error(self, mock_services):
        """Test before_run when job record not found."""

        processor = CropMainFilesWorker(
            job_id=1,
            user={"username": "test"},
        )

        mock_services["update_job_status"].side_effect = LookupError("Job not found")

        result = processor.before_run()

        assert result is False


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

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        result = processor._load_templates()

        assert len(result) == 2
        assert all(t.last_world_file is not None for t in result)

    def test_apply_limits_with_upload_limit(self, mock_services):
        """Test _apply_limits respects upload_limit setting."""
        templates = [
            TemplateRecord(id=1, title="Template:Test1", main_file="test1.svg", last_world_file="test1_2020.svg"),
            TemplateRecord(id=2, title="Template:Test2", main_file="test2.svg", last_world_file="test2_2020.svg"),
            TemplateRecord(id=3, title="Template:Test3", main_file="test3.svg", last_world_file="test3_2020.svg"),
        ]

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
            args={"upload_limit": 2},
        )

        result = processor._apply_limits(templates)

        assert len(result) == 2


class TestCropMainFilesProcessorSteps:
    """Tests for individual pipeline steps."""

    def test_step_download_success(self, mock_services, tmp_path):
        """Test _step_download with successful download."""
        mock_services["download_file"].return_value = {"success": True, "path": str(tmp_path / "test.svg")}

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        file_info = TemplateProcessingInfo(
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
        assert processor.result["summary"]["processed"] == 0  # processed is now under _process_template

    def test_step_download_failure(self, mock_services):
        """Test _step_download when download fails."""
        mock_services["download_file"].return_value = {"success": False, "error": "Network error"}

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        file_info = TemplateProcessingInfo(
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
        assert processor.result["summary"]["failed"] == 1

    def test_step_download_exception(self, mock_services):
        """Test _step_download when exception occurs."""
        mock_services["download_file"].side_effect = ConnectionError("Connection refused")

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        file_info = TemplateProcessingInfo(
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

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        file_info = TemplateProcessingInfo(
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
        assert processor.result["summary"]["cropped"] == 1

    def test_step_crop_failure(self, mock_services, tmp_path):
        """Test _step_crop when crop fails."""
        mock_services["crop_svg_file"].return_value = {"success": False, "error": "Invalid SVG"}

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        file_info = TemplateProcessingInfo(
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
        assert processor.result["summary"]["failed"] == 1

    def test_step_upload_success(self, mock_services, tmp_path):
        """Test _step_upload with successful upload."""
        mock_services["MwClientPage"].return_value.get_text.return_value = "Original file text"
        mock_services["upload_cropped_file"].return_value = {"success": True}

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )
        processor.site = MagicMock()

        file_info = TemplateProcessingInfo(
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
        assert processor.result["summary"]["uploaded"] == 1

    def test_step_upload_file_exists(self, mock_services, tmp_path):
        """Test _step_upload when file already exists."""
        mock_services["MwClientPage"].return_value.get_text.return_value = "Original file text"
        mock_services["upload_cropped_file"].return_value = {"success": False, "file_exists": True}

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )
        processor.site = MagicMock()

        file_info = TemplateProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )
        file_info.cropped_path = tmp_path / "test (cropped).svg"

        result = processor._step_upload(file_info)

        assert result is None  # Should continue to wikitext updates
        assert file_info.status == "skipped"
        assert processor.result["summary"]["skipped"] == 1

    def test_step_upload_failure(self, mock_services, tmp_path):
        """Test _step_upload when upload fails."""
        mock_services["MwClientPage"].return_value.get_text.return_value = "Original file text"
        mock_services["upload_cropped_file"].return_value = {"success": False, "error": "Upload failed"}

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )
        processor.site = MagicMock()

        file_info = TemplateProcessingInfo(
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
        assert processor.result["summary"]["failed"] == 1

    def test_step_update_original_no_change(self, mock_services):
        """Test _step_update_original when no update is needed."""
        mock_services["MwClientPage"].return_value.get_text.return_value = "Original file text"
        mock_services["update_original_file_text"].return_value = "Original file text"  # No change

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )
        processor.site = MagicMock()

        file_info = TemplateProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._step_update_original(file_info)

        assert file_info.steps["update_original"]["result"] is None
        assert file_info.steps["update_original"]["msg"] == "No update needed"
        mock_services["MwClientPage"].return_value.edit.assert_not_called()

    def test_step_update_original_with_update(self, mock_services):
        """Test _step_update_original when update is performed."""
        mock_services["MwClientPage"].return_value.get_text.return_value = "Original file text"
        mock_services["update_original_file_text"].return_value = "Updated file text"
        mock_services["MwClientPage"].return_value.edit.return_value = {"success": True}

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )
        processor.site = MagicMock()

        file_info = TemplateProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._step_update_original(file_info)

        assert file_info.steps["update_original"]["result"] is True
        mock_services["MwClientPage"].return_value.edit.assert_called_once()

    def test_step_update_original_update_fails(self, mock_services):
        """Test _step_update_original when update fails."""
        mock_services["MwClientPage"].return_value.get_text.return_value = "Original file text"
        mock_services["update_original_file_text"].return_value = "Updated file text"
        mock_services["MwClientPage"].return_value.edit.return_value = {"success": False, "error": "Edit conflict"}

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )
        processor.site = MagicMock()

        file_info = TemplateProcessingInfo(
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
        mock_services["MwClientPage"].return_value.get_text.return_value = "Template text"
        mock_services["update_template_page_file_reference"].return_value = "Template text"  # No change

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )
        processor.site = MagicMock()

        file_info = TemplateProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._step_update_template(file_info)

        assert file_info.steps["update_template"]["result"] is None
        assert file_info.steps["update_template"]["msg"] == "No update needed"
        mock_services["MwClientPage"].return_value.edit.assert_not_called()

    def test_step_update_template_with_update(self, mock_services):
        """Test _step_update_template when update is performed."""
        mock_services["MwClientPage"].return_value.get_text.return_value = "Template text"
        mock_services["update_template_page_file_reference"].return_value = "Updated template text"
        mock_services["MwClientPage"].return_value.edit.return_value = {"success": True}

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )
        processor.site = MagicMock()

        file_info = TemplateProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._step_update_template(file_info)

        assert file_info.steps["update_template"]["result"] is True
        mock_services["MwClientPage"].return_value.edit.assert_called_once()


class TestCropMainFilesProcessorHelpers:
    """Tests for helper methods."""

    def test_fail_updates_status_and_result(self, mock_services):
        """Test _fail updates info status and result summary."""

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        file_info = TemplateProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._fail(file_info, "download", "Download failed")

        assert file_info.status == "failed"
        assert file_info.error == "Download failed"
        assert file_info.steps["download"]["result"] is False
        assert processor.result["summary"]["failed"] == 1

    def test_skip_step_updates_step_status(self, mock_services):
        """Test _skip_step updates step status."""

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        file_info = TemplateProcessingInfo(
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

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        file_info = TemplateProcessingInfo(
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
        assert processor.result["summary"]["skipped"] == 1
        assert file_info.cropped_filename is None

    def test_is_cancelled_with_event(self, mock_services):
        """Test is_cancelled with cancel event."""
        cancel_event = threading.Event()

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
            cancel_event=cancel_event,
        )

        assert processor.is_cancelled(check_db=True) is False

        cancel_event.set()
        assert processor.is_cancelled(check_db=True) is True
        assert processor.result["status"] == "cancelled"

    def test_is_cancelled_with_global_check(self, mock_services):
        """Test is_cancelled with global job cancellation check."""
        mock_services["is_job_cancelled"].return_value = True

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        assert processor.is_cancelled(check_db=True) is True
        assert processor.result["status"] == "cancelled"

    def test_append_adds_to_result(self, mock_services):
        """Test _append adds info to pages_processed list."""

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        file_info = TemplateProcessingInfo(
            template_id=1,
            template_title="Template:Test",
            original_file="File:test.svg",
            cropped_filename="File:test (cropped).svg",
        )

        processor._append(file_info)

        assert "pages_processed" in processor.result.keys()
        assert processor.result["pages_processed"] != []
        assert len(processor.result["pages_processed"]) == 1
        assert processor.result["pages_processed"][0]["template_id"] == 1

    def test_get_priority(self, mock_services):
        """Test get_priority calculates correct interval."""

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
        )

        assert processor.get_priority(5) == 1
        assert processor.get_priority(10) == 1
        assert processor.get_priority(25) == 2
        assert processor.get_priority(100) == 10
        assert processor.get_priority(200) == 10


class TestCropMainFilesProcessorProcessTemplate:
    """Tests for _process_template method."""

    def test_process_template_file_already_exists(self, mock_services, mock_site_pages):
        """Test processing when cropped file already exists on Commons."""
        _site = mock_site_pages(True)
        mock_services["get_user_site"].return_value = _site
        mock_services["MwClientPage"].return_value.exists.return_value = True
        mock_services["update_original_file_text"].return_value = "Updated original"
        mock_services["MwClientPage"].return_value.edit.return_value = {"success": True}
        mock_services["MwClientPage"].return_value.get_text.return_value = "Template text"
        mock_services["update_template_page_file_reference"].return_value = "Updated template"
        mock_services["MwClientPage"].return_value.edit.return_value = {"success": True}

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
            args={"upload_files": True},
        )
        processor.site = _site

        template = TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file="test_2020.svg")

        processor._process_template(template)

        # Should skip download, crop, and upload steps
        assert "pages_updated" in processor.result.keys()
        assert processor.result["pages_updated"] != []
        assert processor.result["pages_updated"][0]["steps"]["download"]["result"] is None
        assert "Skipped" in processor.result["pages_updated"][0]["steps"]["download"]["msg"]

    def test_process_template_full_pipeline(self, mock_services, tmp_path, mock_site_pages):
        """Test full pipeline for a new file."""

        _site = mock_site_pages(False)
        mock_services["get_user_site"].return_value = _site
        mock_services["download_file"].return_value = {"success": True, "path": str(tmp_path / "test.svg")}
        mock_services["crop_svg_file"].return_value = {"success": True}
        mock_services["MwClientPage"].return_value.get_text.return_value = "Original file text"
        mock_services["upload_cropped_file"].return_value = {"success": True}
        mock_services["update_original_file_text"].return_value = "Updated original"
        mock_services["MwClientPage"].return_value.get_text.return_value = "Template text"
        mock_services["update_template_page_file_reference"].return_value = "Updated template"
        mock_services["MwClientPage"].return_value.edit.return_value = {"success": True}

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
            args={"upload_files": True},
        )
        processor.site = _site
        processor.original_dir = tmp_path / "original"
        processor.cropped_dir = tmp_path / "cropped"

        template = TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file="test_2020.svg")

        processor._process_template(template)

        file_result = processor.result["pages_uploaded"][0]
        assert file_result["steps"]["download"]["result"] is True
        assert file_result["steps"]["crop"]["result"] is True
        assert file_result["steps"]["upload_cropped"]["result"] is True

    def test_process_template_upload_disabled(self, mock_services, tmp_path, mock_site_pages):
        """Test processing when upload_files is False."""

        mock_services["download_file"].return_value = {"success": True, "path": str(tmp_path / "test.svg")}
        mock_services["crop_svg_file"].return_value = {"success": True}

        processor = CropMainFilesWorker(
            job_id=1,
            user=None,
            args={"upload_files": False},
        )
        _site = mock_site_pages(False)
        processor.site = _site
        processor.original_dir = tmp_path / "original"
        processor.cropped_dir = tmp_path / "cropped"

        template = TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file="test_2020.svg")

        processor._process_template(template)

        # Should skip upload steps
        assert "pages_skipped" in processor.result.keys()
        assert processor.result["pages_skipped"] != []
        assert processor.result["pages_skipped"][0]["steps"]["upload_cropped"]["result"] is None
        assert "upload disabled" in processor.result["pages_skipped"][0]["steps"]["upload_cropped"]["msg"].lower()
        assert processor.result["summary"]["skipped"] == 1


class TestCropMainFilesProcessorRun:
    """Tests for run method."""

    def test_run_full_workflow(self, mock_services, tmp_path, mock_site_pages):
        """Test complete run workflow."""
        _site = mock_site_pages(False)

        mock_services["get_user_site"].return_value = _site

        mock_services["create_commons_session"].return_value = MagicMock()
        mock_services["list_templates"].return_value = [
            TemplateRecord(id=1, title="Template:Test", main_file="test.svg", last_world_file="test_2020.svg"),
        ]
        mock_services["download_file"].return_value = {"success": True, "path": str(tmp_path / "test.svg")}
        mock_services["crop_svg_file"].return_value = {"success": True}
        mock_services["upload_cropped_file"].return_value = {"success": True}
        mock_services["update_original_file_text"].return_value = "Updated original"
        mock_services["MwClientPage"].return_value.get_text.return_value = "Template text"
        mock_services["update_template_page_file_reference"].return_value = "Updated template"
        mock_services["MwClientPage"].return_value.edit.return_value = {"success": True}

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
