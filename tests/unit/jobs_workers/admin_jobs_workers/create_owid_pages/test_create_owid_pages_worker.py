"""Unit tests for create_owid_pages/worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker import (
    CreateOwidPagesWorker,
    TemplateProcessingInfo,
    create_owid_pages_for_templates,
)


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    """Mock the services used by create_owid_pages worker."""

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
    mock_is_cancelled = MagicMock(return_value=False)
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.is_job_cancelled",
        mock_is_cancelled,
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
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker.list_templates",
        mock_list_templates,
    )

    # Mock get_user_site
    mock_get_user_site = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker.get_user_site",
        mock_get_user_site,
    )

    # Mock API services
    mock_mwclientpage = MagicMock()
    mock_page_instance = MagicMock()
    mock_mwclientpage.return_value = mock_page_instance
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker.MwClientPage", mock_mwclientpage
    )

    # Mock create_new_text
    mock_create_new_text = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker.create_new_text",
        mock_create_new_text,
    )

    # Mock is_pages_exists (called by filter_created)
    mock_is_pages_exists = MagicMock(return_value={})
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker.is_pages_exists",
        mock_is_pages_exists,
    )

    # Mock merge_categories and sort_categories (called in _step_update)
    mock_merge_categories = MagicMock(side_effect=lambda current, new: new)
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker.merge_categories",
        mock_merge_categories,
    )
    mock_sort_categories = MagicMock(side_effect=lambda text: text)
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.create_owid_pages.worker.sort_categories",
        mock_sort_categories,
    )

    # Mock is_job_cancelled_file_exist (called by is_cancelled in BaseObjectsJobWorker)
    mock_is_job_cancelled_file_exist = MagicMock(return_value=False)
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.is_job_cancelled_file_exist",
        mock_is_job_cancelled_file_exist,
    )

    return {
        "MwClientPage": mock_mwclientpage,
        "page_instance": mock_page_instance,
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "generate_result_file_name": mock_generate_result_file_name,
        "list_templates": mock_list_templates,
        "get_user_site": mock_get_user_site,
        "create_new_text": mock_create_new_text,
        "is_job_cancelled": mock_is_cancelled,
        "is_pages_exists": mock_is_pages_exists,
        "merge_categories": mock_merge_categories,
        "sort_categories": mock_sort_categories,
        "is_job_cancelled_file_exist": mock_is_job_cancelled_file_exist,
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

    def test_worker_initialization_reads_limit_items_from_args(self, mock_services):
        """Test worker reads limit_items from args."""
        worker = CreateOwidPagesWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"limit_items": 5},
        )

        assert worker.limit_items == 5

    def test_worker_initialization_defaults_limit_items_when_args_none(self, mock_services):
        """Test worker defaults limit_items to 0 when args is None."""
        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None, args=None)

        assert worker.limit_items == 0

    def test_worker_initialization_limit_items_none_when_key_missing(self, mock_services):
        """Test worker sets limit_items to 0 when args has no limit_items key."""
        worker = CreateOwidPagesWorker(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"other_key": "value"},
        )

        assert worker.limit_items == 0

    def test_get_job_type(self, mock_services):
        """Test get_job_type returns correct value."""
        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        assert worker.get_job_type() == "create_owid_pages"

    def test_get_initial_result(self, mock_services):
        """Test initial result matching expected structure."""
        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker.result

        assert result.status == "pending"
        assert result.started_at is not None
        assert result.completed_at is None
        assert result.cancelled_at is None
        assert result.summary.total == 0
        assert result.summary.processed == 0
        assert result.summary.created == 0
        assert result.summary.updated == 0
        assert result.summary.failed == 0
        assert result.summary.skipped == 0
        assert result.pages_processed == []


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
        """Test _apply_limits respects the limit_items setting."""
        templates = [
            TemplateRecord(id=1, title="Template:OWID/Test1", main_file="test1.svg", last_world_file=None),
            TemplateRecord(id=2, title="Template:OWID/Test2", main_file="test2.svg", last_world_file=None),
            TemplateRecord(id=3, title="Template:OWID/Test3", main_file="test3.svg", last_world_file=None),
        ]

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None, args={"limit_items": 2})
        result = worker._apply_limits(templates)

        assert len(result) == 2

    def test_apply_limits_with_zero_limit(self, mock_services):
        """Test _apply_limits with zero limit returns all templates."""
        templates = [
            TemplateRecord(id=1, title="Template:OWID/Test1", main_file="test1.svg", last_world_file=None),
            TemplateRecord(id=2, title="Template:OWID/Test2", main_file="test2.svg", last_world_file=None),
        ]

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker._apply_limits(templates)

        assert len(result) == 2

    def test_apply_limits_with_limit_greater_than_templates(self, mock_services):
        """Test _apply_limits when limit is greater than number of templates."""
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
        mock_services["MwClientPage"].return_value.get_text.return_value = "Template wikitext content"

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.site = MagicMock()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")

        result = worker._step_load_template_text(info)

        assert result is True
        assert info._template_text == "Template wikitext content"
        assert info.steps["load_template_text"]["result"] is True

    def test_step_load_template_text_failure(self, mock_services):
        """Test _step_load_template_text when text retrieval fails."""
        mock_services["MwClientPage"].return_value.get_text.return_value = ""

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.site = MagicMock()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")

        result = worker._step_load_template_text(info)

        assert result is False
        assert info.status == "failed"
        assert info.steps["load_template_text"]["result"] is False
        assert worker.result.summary.failed == 1


class TestCreateNewTextStep:
    def test_step_create_new_text_success(self, mock_services):
        """Test _step_create_new_text with successful text generation."""
        mock_services["create_new_text"].return_value = "New OWID page content"

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
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
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._template_text = "Template content"

        result = worker._step_create_new_text(info)

        assert result is False
        assert info.status == "failed"
        assert info.steps["create_new_text"]["result"] is False
        assert "Invalid template format" in info.steps["create_new_text"]["msg"]


class TestUpdateStep:
    def test_step_update_page_identical_content(self, mock_services):
        """Test _step_update when page has identical content."""
        mock_services["MwClientPage"].return_value.get_text.return_value = "New content"

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._new_text = "New content"

        result = worker._step_update(info, "OWID/Test")

        assert result is None  # Should not continue to create step
        assert info.status == "skipped"
        assert worker.result.summary.skipped == 1

    def test_step_update_page_different_content(self, mock_services):
        """Test _step_update when page has different content."""
        mock_services["MwClientPage"].return_value.get_text.return_value = "Old content"
        mock_services["page_instance"].edit.return_value = {"success": True}

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._new_text = "New content"

        result = worker._step_update(info, "OWID/Test")

        assert result is True
        assert worker.result.summary.updated == 1
        assert info.status == "updated"
        mock_services["page_instance"].edit.assert_called_once()

    def test_step_update_update_fails(self, mock_services):
        """Test _step_update when update fails."""
        mock_services["MwClientPage"].return_value.get_text.return_value = "Old content"
        mock_services["page_instance"].edit.return_value = {"success": False, "error": "Edit conflict"}

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._new_text = "New content"

        result = worker._step_update(info, "OWID/Test")

        assert result is False
        assert info.status == "failed"


class TestCreateNewPageStep:
    def test_step_create_new_page_success(self, mock_services, mock_site):
        """Test _step_create_new_page with successful creation."""
        mock_services["page_instance"].create.return_value = {"success": True}

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.site = mock_site
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._new_text = "New OWID page content"

        result = worker._step_create_new_page(info)

        assert result is True
        assert info.new_page_title == "OWID/Test"
        assert info.steps["create_new_page"]["result"] is True
        assert worker.result.summary.created == 1
        mock_services["page_instance"].create.assert_called_once_with(
            "New OWID page content",
            summary="Creating OWID page from [[Template:OWID/Test]]",
        )

    def test_step_create_new_page_failure(self, mock_services):
        """Test _step_create_new_page when creation fails."""
        mock_services["page_instance"].create.return_value = {"success": False, "error": "Permission denied"}

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        worker.site = MagicMock()
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")
        info._new_text = "New OWID page content"

        result = worker._step_create_new_page(info)

        assert result is False
        assert info.status == "failed"
        assert info.error == "Permission denied"
        assert worker.result.summary.failed == 1


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
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")

        worker._fail(info, "load_template_text", "Failed to load")

        assert info.status == "failed"
        assert info.error == "Failed to load"
        assert info.steps["load_template_text"]["result"] is False
        assert info.steps["load_template_text"]["msg"] == "Failed to load"
        assert worker.result.summary.failed == 1

    def test_skip_step_updates_step_status(self, mock_services):
        """Test _skip_step updates step status."""
        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        info = TemplateProcessingInfo(template_id=1, template_title="Template:OWID/Test")

        worker._skip_step(info, "create_new_page", "Already exists")

        assert info.steps["create_new_page"]["result"] is None
        assert info.steps["create_new_page"]["msg"] == "Already exists"


class TestCreateOwidPagesWorkerProcess:
    """Tests for the main process method."""

    def test_process_no_site_authentication(self, mock_services, monkeypatch: pytest.MonkeyPatch):
        """Test process when site authentication fails."""
        mock_services["get_user_site"].return_value = None
        # Bypass update_job_status
        monkeypatch.setattr("src.main_app.jobs_workers.base_worker.update_job_status", MagicMock())
        monkeypatch.setattr("src.main_app.jobs_workers.base_worker.save_job_result_by_name", MagicMock())

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        assert result.status == "failed"
        assert result.failed_at is not None

    def test_process_no_templates(self, mock_services, monkeypatch: pytest.MonkeyPatch):
        """Test process when there are no templates to process."""
        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["list_templates"].return_value = []
        # Bypass update_job_status
        monkeypatch.setattr("src.main_app.jobs_workers.base_worker.update_job_status", MagicMock())
        monkeypatch.setattr("src.main_app.jobs_workers.base_worker.save_job_result_by_name", MagicMock())

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        assert result.status == "skipped"
        assert result.summary.total == 0
        assert result.summary.processed == 0

    def test_process_single_template_success(self, mock_services, monkeypatch: pytest.MonkeyPatch):
        """Test process with a single successful template."""
        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["list_templates"].return_value = [
            TemplateRecord(id=1, title="Template:OWID/Test", main_file="test.svg", last_world_file=None)
        ]
        mock_services["MwClientPage"].return_value.get_text.return_value = "Template content"
        mock_services["create_new_text"].return_value = "New OWID content"
        mock_services["page_instance"].exists.return_value = False
        mock_services["page_instance"].create.return_value = {"success": True}

        # Bypass update_job_status
        monkeypatch.setattr("src.main_app.jobs_workers.base_worker.update_job_status", MagicMock())
        monkeypatch.setattr("src.main_app.jobs_workers.base_worker.save_job_result_by_name", MagicMock())

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        assert result.status == "completed"
        assert result.summary.total == 1
        assert result.summary.processed == 1
        assert result.summary.created == 1
        assert result.summary.failed == 0

    def test_process_single_template_skipped(self, mock_services, monkeypatch: pytest.MonkeyPatch):
        """Test process with a skipped template (already exists)."""
        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["list_templates"].return_value = [
            TemplateRecord(id=1, title="Template:OWID/Test", main_file="test.svg", last_world_file=None)
        ]
        mock_services["MwClientPage"].return_value.get_text.return_value = "Template content"
        mock_services["create_new_text"].return_value = "New OWID content"
        mock_services["page_instance"].exists.return_value = True
        mock_services["MwClientPage"].return_value.get_text.return_value = "New OWID content"

        # Bypass update_job_status
        monkeypatch.setattr("src.main_app.jobs_workers.base_worker.update_job_status", MagicMock())
        monkeypatch.setattr("src.main_app.jobs_workers.base_worker.save_job_result_by_name", MagicMock())

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        assert result.status == "completed"
        assert result.summary.skipped == 1

    def test_process_multiple_templates_mixed_results(self, mock_services, monkeypatch: pytest.MonkeyPatch):
        """Test process with multiple templates having different outcomes."""
        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["list_templates"].return_value = [
            TemplateRecord(id=1, title="Template:OWID/Test1", main_file="test1.svg", last_world_file=None),
            TemplateRecord(id=2, title="Template:OWID/Test2", main_file="test2.svg", last_world_file=None),
            TemplateRecord(id=3, title="Template:OWID/Test3", main_file="test3.svg", last_world_file=None),
        ]

        # First succeeds, second fails text load, third succeeds
        def _mwclientpage_side_effect(title, site):
            instance = MagicMock()
            if "Test2" in title:
                instance.get_text.return_value = ""
            else:
                instance.get_text.return_value = f"Content for {title}"
            instance.exists.return_value = False
            instance.create.return_value = {"success": True}
            return instance

        mock_services["MwClientPage"].side_effect = _mwclientpage_side_effect
        mock_services["create_new_text"].return_value = "New OWID content"

        # Bypass update_job_status
        monkeypatch.setattr("src.main_app.jobs_workers.base_worker.update_job_status", MagicMock())
        monkeypatch.setattr("src.main_app.jobs_workers.base_worker.save_job_result_by_name", MagicMock())

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=None)
        result = worker.process()

        assert result.summary.total == 3
        assert result.summary.processed == 3
        assert result.summary.failed == 1
        assert result.summary.created == 2

    def test_process_with_cancellation(self, mock_services, monkeypatch: pytest.MonkeyPatch):
        """Test process respects cancellation event."""
        cancel_event = threading.Event()

        mock_services["get_user_site"].return_value = MagicMock()
        mock_services["list_templates"].return_value = [
            TemplateRecord(id=1, title="Template:OWID/Test1", main_file="test1.svg", last_world_file=None),
            TemplateRecord(id=2, title="Template:OWID/Test2", main_file="test2.svg", last_world_file=None),
        ]
        mock_services["MwClientPage"].return_value.get_text.return_value = "Template content"
        mock_services["create_new_text"].return_value = "New OWID content"
        mock_services["page_instance"].exists.return_value = False
        mock_services["page_instance"].create.return_value = {"success": True}
        mock_services["is_job_cancelled"].return_value = True

        # Bypass update_job_status
        monkeypatch.setattr("src.main_app.jobs_workers.base_worker.update_job_status", MagicMock())
        monkeypatch.setattr("src.main_app.jobs_workers.base_worker.save_job_result_by_name", MagicMock())

        worker = CreateOwidPagesWorker(job_id=1, user=None, cancel_event=cancel_event)

        # Set cancelled after first template
        call_count = [0]
        original_is_cancelled = worker.is_cancelled

        def patched_is_cancelled(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 1:
                worker._mark_as_cancelled_in_result()
                return True
            return original_is_cancelled(*args, **kwargs)

        worker.is_cancelled = patched_is_cancelled

        result = worker.process()

        # Should stop early due to cancellation
        assert result.status == "cancelled"


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
            create_owid_pages_for_templates(job_id=1, user=None, cancel_event=cancel_event)

        mock_run.assert_called_once()

    def test_entry_point_accepts_args_keyword_param(self, mock_services):
        """Test that the entry point accepts args= keyword-only param (unified signature)."""
        with patch.object(CreateOwidPagesWorker, "run") as mock_run:
            mock_run.return_value = {"status": "completed"}
            # Should not raise TypeError; args is accepted but unused
            create_owid_pages_for_templates(job_id=1, user=None, args={"some_key": "value"})

        mock_run.assert_called_once()

    def test_entry_point_args_defaults_to_none(self, mock_services):
        """Test that args defaults to None and the entry point works without it."""
        with patch.object(CreateOwidPagesWorker, "run") as mock_run:
            mock_run.return_value = {"status": "completed"}
            create_owid_pages_for_templates(job_id=99, user=None)

        mock_run.assert_called_once()

    def test_entry_point_maps_create_owid_pages_limit_to_limit_items(self, mock_services):
        """Test that limit_items is mapped to limit_items in args."""
        with patch.object(CreateOwidPagesWorker, "__init__", return_value=None) as mock_init:
            with patch.object(CreateOwidPagesWorker, "run") as mock_run:
                mock_run.return_value = {"status": "completed"}
                create_owid_pages_for_templates(
                    job_id=1,
                    user=None,
                    args={"limit_items": 5},
                )

        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["args"]["limit_items"] == 5

    def test_entry_point_does_not_map_when_key_absent(self, mock_services):
        """Test that args are passed unchanged when limit_items is absent."""
        with patch.object(CreateOwidPagesWorker, "__init__", return_value=None) as mock_init:
            with patch.object(CreateOwidPagesWorker, "run") as mock_run:
                mock_run.return_value = {"status": "completed"}
                create_owid_pages_for_templates(
                    job_id=1,
                    user=None,
                    args={"other_key": "value"},
                )

        call_kwargs = mock_init.call_args.kwargs
        assert "limit_items" not in call_kwargs["args"]

    def test_entry_point_does_not_modify_args_when_args_is_none(self, mock_services):
        """Test that entry point works correctly when args is None."""
        with patch.object(CreateOwidPagesWorker, "__init__", return_value=None) as mock_init:
            with patch.object(CreateOwidPagesWorker, "run") as mock_run:
                mock_run.return_value = {"status": "completed"}
                create_owid_pages_for_templates(job_id=1, user=None, args=None)

        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["args"] is None
