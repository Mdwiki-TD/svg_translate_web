"""Unit tests for create_owid_pages/worker module."""

from __future__ import annotations

import threading
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.create_owid_pages.worker import (
    CreateOwidPagesWorker,
    TemplateProcessingInfo,
    create_owid_pages_for_templates,
)
from src.main_app.services.template_service import TemplateRecord


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch, mock_jobs_service):
    """Mock the services used by create_owid_pages worker."""

    # Mock jobs_service
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.jobs_service.update_job_status",
        mock_update_job_status,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.jobs_service.save_job_result_by_name",
        mock_save_job_result,
    )

    # Mock generate_result_file_name
    mock_generate_result_file_name = MagicMock(side_effect=lambda job_id, job_type: f"{job_type}_job_{job_id}.json")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.generate_result_file_name",
        mock_generate_result_file_name,
    )

    # Mock template_service
    mock_list_templates = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.create_owid_pages.worker.template_service.list_templates",
        mock_list_templates,
    )

    # Mock get_user_site
    mock_get_user_site = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.create_owid_pages.worker.get_user_site",
        mock_get_user_site,
    )

    # Mock API services
    mock_get_page_text = MagicMock()
    mock_is_page_exists = MagicMock()
    mock_create_page = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.create_owid_pages.worker.get_page_text",
        mock_get_page_text,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.create_owid_pages.worker.is_page_exists",
        mock_is_page_exists,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.create_owid_pages.worker.create_page",
        mock_create_page,
    )

    # Mock create_new_text
    mock_create_new_text = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.create_owid_pages.worker.create_new_text",
        mock_create_new_text,
    )

    # Mock settings
    mock_settings = MagicMock()
    mock_settings.dynamic = {}
    monkeypatch.setattr(
        "src.main_app.jobs_workers.create_owid_pages.worker.settings",
        mock_settings,
    )

    return {
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "generate_result_file_name": mock_generate_result_file_name,
        "list_templates": mock_list_templates,
        "get_user_site": mock_get_user_site,
        "get_page_text": mock_get_page_text,
        "is_page_exists": mock_is_page_exists,
        "create_page": mock_create_page,
        "create_new_text": mock_create_new_text,
        "settings": mock_settings,
        "is_job_cancelled": mock_jobs_service,
    }


class TestTemplateProcessingInfo:
    """Tests for TemplateProcessingInfo dataclass."""

    def test_default_initialization(self):
        """Test TemplateProcessingInfo initializes with correct defaults."""
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")

        assert info.template_id == 1
        assert info.template_title == "Template:OWID/Test"
        assert info.new_page_title is None
        assert info.status == "pending"
        assert info.error is None
        assert info._template_text is None
        assert info._new_text is None
        assert "load_template_text" in info.steps
        assert "create_new_text" in info.steps
        assert "create_new_page" in info.steps

    def test_to_dict(self):
        """Test to_dict serialization."""
        info = TemplateProcessingInfo(
            template_id=1,
            template_title="Template:OWID/Test",
            new_page_title="OWID/Test",
            status="completed",
            error="Test error",
        )
        info.steps["load_template_text"] = {"result": True, "msg": "Loaded"}

        result = info.to_dict()

        assert result["template_id"] == 1
        assert result["template_title"] == "Template:OWID/Test"
        assert result["new_page_title"] == "OWID/Test"
        assert result["status"] == "completed"
        assert result["error"] == "Test error"
        assert result["steps"]["load_template_text"]["result"] is True


class TestCreateOwidPagesWorkerInitialization:
    """Tests for CreateOwidPagesWorker initialization."""

    def test_worker_initialization(self, mock_services):
        """Test worker initializes correctly."""
        worker = CreateOwidPagesWorker(job_id=1, user={"username": "test"}, cancel_event=None)

        assert worker.job_id == 1
        assert worker.user == {"username": "test"}
        assert worker.site is None
        assert worker.get_job_type() == "create_owid_pages"

    def test_get_job_type(self, mock_services):
        """Test get_job_type returns correct value."""
        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        assert worker.get_job_type() == "create_owid_pages"

    def test_get_initial_result(self, mock_services):
        """Test get_initial_result returns proper structure."""
        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker.get_initial_result()

        assert result["status"] == "pending"
        assert "started_at" in result
        assert result["completed_at"] is None
        assert result["cancelled_at"] is None
        assert result["summary"]["total"] == 0
        assert result["summary"]["processed"] == 0
        assert result["summary"]["created"] == 0
        assert result["summary"]["updated"] == 0
        assert result["summary"]["failed"] == 0
        assert result["summary"]["skipped"] == 0
        assert result["templates_processed"] == []


class TestCreateOwidPagesWorkerLoadTemplates:
    """Tests for _load_templates and _apply_limits."""

    def test_load_templates_filters_owid_prefix(self, mock_services):
        """Test that only templates with 'Template:OWID/' prefix are loaded."""
        templates = [
            TemplateRecord(id=1, title="Template:OWID/Test1", main_file="test1.svg", last_world_file=None),
            TemplateRecord(id=2, title="Template:Other/Test2", main_file="test2.svg", last_world_file=None),
            TemplateRecord(id=3, title="Template:OWID/Test3", main_file="test3.svg", last_world_file=None),
        ]
        mock_services["list_templates"].return_value = templates

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker._load_templates()

        assert len(result) == 2
        assert all(t.title.startswith("Template:OWID/") for t in result)

    def test_load_templates_returns_empty_when_no_owid_templates(self, mock_services):
        """Test that empty list is returned when no OWID templates exist."""
        templates = [
            TemplateRecord(id=1, title="Template:Other/Test1", main_file="test1.svg", last_world_file=None),
        ]
        mock_services["list_templates"].return_value = templates

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker._load_templates()

        assert result == []

    def test_apply_limits_with_limit_set(self, mock_services):
        """Test _apply_limits respects the create_owid_pages_limit setting."""
        mock_services["settings"].dynamic = {"create_owid_pages_limit": 2}
        templates = [
            TemplateRecord(id=1, title="Template:OWID/Test1", main_file="test1.svg", last_world_file=None),
            TemplateRecord(id=2, title="Template:OWID/Test2", main_file="test2.svg", last_world_file=None),
            TemplateRecord(id=3, title="Template:OWID/Test3", main_file="test3.svg", last_world_file=None),
        ]

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker._apply_limits(templates)

        assert len(result) == 2

    def test_apply_limits_with_zero_limit(self, mock_services):
        """Test _apply_limits with zero limit returns all templates."""
        mock_services["settings"].dynamic = {"create_owid_pages_limit": 0}
        templates = [
            TemplateRecord(id=1, title="Template:OWID/Test1", main_file="test1.svg", last_world_file=None),
            TemplateRecord(id=2, title="Template:OWID/Test2", main_file="test2.svg", last_world_file=None),
        ]

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker._apply_limits(templates)

        assert len(result) == 2

    def test_apply_limits_with_limit_greater_than_templates(self, mock_services):
        """Test _apply_limits when limit is greater than number of templates."""
        mock_services["settings"].dynamic = {"create_owid_pages_limit": 10}
        templates = [
            TemplateRecord(id=1, title="Template:OWID/Test1", main_file="test1.svg", last_world_file=None),
        ]

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker._apply_limits(templates)

        assert len(result) == 1


class TestCreateOwidPagesWorkerSteps:
    """Tests for individual pipeline steps."""

    def test_step_load_template_text_success(self, mock_services):
        """Test _step_load_template_text with successful text retrieval."""
        mock_services["get_page_text"].return_value = "Template wikitext content"

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.site = MagicMock()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")

        result = worker._step_load_template_text(info)

        assert result is True
        assert info._template_text == "Template wikitext content"
        assert info.steps["load_template_text"]["result"] is True

    def test_step_load_template_text_failure(self, mock_services):
        """Test _step_load_template_text when text retrieval fails."""
        mock_services["get_page_text"].return_value = ""

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.result = worker.get_initial_result()
        worker.site = MagicMock()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")

        result = worker._step_load_template_text(info)

        assert result is False
        assert info.status == "failed"
        assert info.steps["load_template_text"]["result"] is False
        assert worker.result["summary"]["failed"] == 1

    def test_step_create_new_text_success(self, mock_services):
        """Test _step_create_new_text with successful text generation."""
        mock_services["create_new_text"].return_value = "New OWID page content"

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.result = worker.get_initial_result()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._template_text = "Template content"

        result = worker._step_create_new_text(info)

        assert result is True
        assert info._new_text == "New OWID page content"
        assert info.steps["create_new_text"]["result"] is True
        mock_services["create_new_text"].assert_called_once_with("Template content", "Template:OWID/Test")

    def test_step_create_new_text_exception(self, mock_services):
        """Test _step_create_new_text when exception occurs."""
        mock_services["create_new_text"].side_effect = ValueError("Invalid template format")

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.result = worker.get_initial_result()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._template_text = "Template content"

        result = worker._step_create_new_text(info)

        assert result is False
        assert info.status == "failed"
        assert info.steps["create_new_text"]["result"] is False
        assert "Invalid template format" in info.steps["create_new_text"]["msg"]

    def test_step_check_exists_and_update_page_not_exists(self, mock_services):
        """Test _step_check_exists_and_update when page does not exist."""
        mock_services["is_page_exists"].return_value = False

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.result = worker.get_initial_result()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._new_text = "New content"

        result = worker._step_check_exists_and_update(info)

        assert result is True  # Should continue to create step
        mock_services["is_page_exists"].assert_called_once_with("OWID/Test", None)

    def test_step_check_exists_and_update_page_identical_content(self, mock_services):
        """Test _step_check_exists_and_update when page has identical content."""
        mock_services["is_page_exists"].return_value = True
        mock_services["get_page_text"].return_value = "New content"

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.result = worker.get_initial_result()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._new_text = "New content"

        result = worker._step_check_exists_and_update(info)

        assert result is False  # Should not continue to create step
        assert info.status == "skipped"
        assert worker.result["summary"]["skipped"] == 1
        assert worker.result["summary"]["processed"] == 1

    def test_step_check_exists_and_update_page_different_content(self, mock_services):
        """Test _step_check_exists_and_update when page has different content."""
        mock_services["is_page_exists"].return_value = True
        mock_services["get_page_text"].return_value = "Old content"
        mock_services["create_page"].return_value = {"success": True}

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.result = worker.get_initial_result()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._new_text = "New content"

        result = worker._step_check_exists_and_update(info)

        assert result is False  # Should not continue to create step (already updated)
        assert worker.result["summary"]["updated"] == 1
        assert worker.result["summary"]["processed"] == 1
        assert info.status == "completed"
        mock_services["create_page"].assert_called_once()

    def test_step_check_exists_and_update_update_fails(self, mock_services):
        """Test _step_check_exists_and_update when update fails."""
        mock_services["is_page_exists"].return_value = True
        mock_services["get_page_text"].return_value = "Old content"
        mock_services["create_page"].return_value = {"success": False, "error": "Edit conflict"}

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.result = worker.get_initial_result()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._new_text = "New content"

        result = worker._step_check_exists_and_update(info)

        assert result is False
        assert info.status == "failed"
        assert info.steps["create_new_page"]["result"] is False

    def test_step_create_new_page_success(self, mock_services):
        """Test _step_create_new_page with successful creation."""
        mock_services["create_page"].return_value = {"success": True}

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.result = worker.get_initial_result()
        mock_site = MagicMock()
        worker.site = mock_site
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._new_text = "New OWID page content"

        result = worker._step_create_new_page(info)

        assert result is True
        assert info.new_page_title == "OWID/Test"
        assert info.steps["create_new_page"]["result"] is True
        assert worker.result["summary"]["created"] == 1
        mock_services["create_page"].assert_called_once_with(
            "OWID/Test",
            "New OWID page content",
            mock_site,
            summary="Creating OWID page from [[Template:OWID/Test]]",
        )

    def test_step_create_new_page_failure(self, mock_services):
        """Test _step_create_new_page when creation fails."""
        mock_services["create_page"].return_value = {"success": False, "error": "Permission denied"}

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.result = worker.get_initial_result()
        worker.site = MagicMock()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._new_text = "New OWID page content"

        result = worker._step_create_new_page(info)

        assert result is False
        assert info.status == "failed"
        assert info.error == "Permission denied"
        assert worker.result["summary"]["failed"] == 1


class TestCreateOwidPagesWorkerHelpers:
    """Tests for helper methods."""

    def test_create_new_page_title_with_owid_prefix(self, mock_services):
        """Test create_new_page_title with Template:OWID/ prefix."""
        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")

        result = worker.create_new_page_title(info)

        assert result == "OWID/Test"

    def test_create_new_page_title_with_other_prefix(self, mock_services):
        """Test create_new_page_title with other Template: prefix."""
        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        info = TemplateProcessingInfo(template_id=1, template_title="Template:Other/Test")

        result = worker.create_new_page_title(info)

        assert result == "OWID/Other/Test"

    def test_fail_updates_status_and_result(self, mock_services):
        """Test _fail updates info status and result summary."""
        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.result = worker.get_initial_result()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")

        worker._fail(info, "load_template_text", "Failed to load")

        assert info.status == "failed"
        assert info.error == "Failed to load"
        assert info.steps["load_template_text"]["result"] is False
        assert info.steps["load_template_text"]["msg"] == "Failed to load"
        assert worker.result["summary"]["failed"] == 1

    def test_skip_step_updates_step_status(self, mock_services):
        """Test _skip_step updates step status."""
        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")

        worker._skip_step(info, "create_new_page", "Already exists")

        assert info.steps["create_new_page"]["result"] is None
        assert info.steps["create_new_page"]["msg"] == "Already exists"

    def test_append_adds_to_result(self, mock_services):
        """Test _append adds info to templates_processed list."""
        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.result = worker.get_initial_result()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")

        worker._append(info)

        assert len(worker.result["templates_processed"]) == 1
        assert worker.result["templates_processed"][0]["template_id"] == 1


class TestCreateOwidPagesWorkerProcess:
    """Tests for the main process method."""

    def test_process_no_site_authentication(self, mock_services):
        """Test process when site authentication fails."""
        mock_services["get_user_site"].return_value = None

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        assert result["status"] == "failed"
        assert "failed_at" in result

    def test_process_no_templates(self, mock_services):
        """Test process when there are no templates to process."""
        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["list_templates"].return_value = []

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        assert result["status"] == "completed"
        assert result["summary"]["total"] == 0
        assert result["summary"]["processed"] == 0

    def test_process_single_template_success(self, mock_services):
        """Test process with a single successful template."""
        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["list_templates"].return_value = [
            TemplateRecord(id=1, title="Template:OWID/Test", main_file="test.svg", last_world_file=None)
        ]
        mock_services["get_page_text"].return_value = "Template content"
        mock_services["create_new_text"].return_value = "New OWID content"
        mock_services["is_page_exists"].return_value = False
        mock_services["create_page"].return_value = {"success": True}

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        assert result["status"] == "completed"
        assert result["summary"]["total"] == 1
        assert result["summary"]["processed"] == 1
        assert result["summary"]["created"] == 1
        assert result["summary"]["failed"] == 0

    def test_process_single_template_skipped(self, mock_services):
        """Test process with a skipped template (already exists)."""
        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["list_templates"].return_value = [
            TemplateRecord(id=1, title="Template:OWID/Test", main_file="test.svg", last_world_file=None)
        ]
        mock_services["get_page_text"].return_value = "Template content"
        mock_services["create_new_text"].return_value = "New OWID content"
        mock_services["is_page_exists"].return_value = True
        mock_services["get_page_text"].return_value = "New OWID content"

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        assert result["status"] == "completed"
        assert result["summary"]["skipped"] == 1

    def test_process_multiple_templates_mixed_results(self, mock_services):
        """Test process with multiple templates having different outcomes."""
        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["list_templates"].return_value = [
            TemplateRecord(id=1, title="Template:OWID/Test1", main_file="test1.svg", last_world_file=None),
            TemplateRecord(id=2, title="Template:OWID/Test2", main_file="test2.svg", last_world_file=None),
            TemplateRecord(id=3, title="Template:OWID/Test3", main_file="test3.svg", last_world_file=None),
        ]

        # First succeeds, second fails text load, third succeeds
        def get_page_text_side_effect(title, site):
            if "Test2" in title:
                return ""
            return f"Content for {title}"

        mock_services["get_page_text"].side_effect = get_page_text_side_effect
        mock_services["create_new_text"].return_value = "New OWID content"
        mock_services["is_page_exists"].return_value = False
        mock_services["create_page"].return_value = {"success": True}

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        assert result["summary"]["total"] == 3
        assert result["summary"]["processed"] == 2
        assert result["summary"]["failed"] == 1
        assert result["summary"]["created"] == 2

    def test_process_with_cancellation(self, mock_services):
        """Test process respects cancellation event."""
        cancel_event = threading.Event()

        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["list_templates"].return_value = [
            TemplateRecord(id=1, title="Template:OWID/Test1", main_file="test1.svg", last_world_file=None),
            TemplateRecord(id=2, title="Template:OWID/Test2", main_file="test2.svg", last_world_file=None),
        ]
        mock_services["get_page_text"].return_value = "Template content"
        mock_services["create_new_text"].return_value = "New OWID content"
        mock_services["is_page_exists"].return_value = False
        mock_services["create_page"].return_value = {"success": True}
        mock_services["is_job_cancelled"].return_value = True

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=cancel_event)

        # Set cancelled after first template
        call_count = [0]
        original_is_cancelled = worker.is_cancelled

        def patched_is_cancelled():
            call_count[0] += 1
            if call_count[0] > 1:
                return True
            return original_is_cancelled()

        worker.is_cancelled = patched_is_cancelled

        result = worker.process()

        # Should stop early due to cancellation
        assert result["status"] == "cancelled"


class TestCreateOwidPagesForTemplates:
    """Tests for create_owid_pages_for_templates entry point."""

    def test_entry_point_creates_worker_and_runs(self, mock_services):
        """Test that create_owid_pages_for_templates creates worker and runs it."""
        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["list_templates"].return_value = []

        with patch.object(CreateOwidPagesWorker, "run") as mock_run:
            mock_run.return_value = {"status": "completed"}
            create_owid_pages_for_templates(job_id=1, user={"username": "test"})

        mock_run.assert_called_once()

    def test_entry_point_with_cancel_event(self, mock_services):
        """Test entry point with cancel event."""
        cancel_event = threading.Event()

        with patch.object(CreateOwidPagesWorker, "run") as mock_run:
            mock_run.return_value = {"status": "completed"}
            create_owid_pages_for_templates(job_id=1, cancel_event=cancel_event)

        mock_run.assert_called_once()
