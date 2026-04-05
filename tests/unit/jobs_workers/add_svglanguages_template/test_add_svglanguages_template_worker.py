"""Unit tests for add_svglanguages_template worker module."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.config import settings
from src.main_app.jobs_workers.add_svglanguages_template.worker import (
    AddSvgSVGLanguagesTemplate,
    TemplateInfo,
    add_svglanguages_template_to_templates,
)


class TestTemplateInfo:
    """Tests for TemplateInfo dataclass."""

    def test_template_info_initialization(self):
        """Test TemplateInfo is initialized with correct defaults."""
        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")

        assert info.template_id == 1
        assert info.template_title == "Template:OWID/test"
        assert info.status == "pending"
        assert info.error is None
        assert info._text is None
        assert info._template_text is None
        assert info._new_text is None
        assert isinstance(info.timestamp, str)

    def test_template_info_steps_initialized(self):
        """Test that steps dictionary is properly initialized."""
        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")

        expected_steps = ["load_template_text", "generate_template_text", "add_template_text", "save_new_text"]
        for step in expected_steps:
            assert step in info.steps
            assert info.steps[step]["result"] is None
            assert info.steps[step]["msg"] == ""

    def test_template_info_to_dict(self):
        """Test TemplateInfo.to_dict() returns correct structure."""
        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info.status = "completed"
        info.steps["load_template_text"] = {"result": True, "msg": "Loaded"}

        result = info.to_dict()

        assert result["template_id"] == 1
        assert result["template_title"] == "Template:OWID/test"
        assert result["status"] == "completed"
        assert result["error"] is None
        assert "timestamp" in result
        assert "steps" in result


class TestAddSvgSVGLanguagesTemplateInit:
    """Tests for AddSvgSVGLanguagesTemplate initialization."""

    def test_worker_initialization(self, mock_jobs_service):
        """Test worker is initialized correctly."""
        user = {"username": "test_user"}
        cancel_event = threading.Event()

        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=user, cancel_event=cancel_event)

        assert worker.job_id == 1
        assert worker.user == user
        assert worker.cancel_event == cancel_event
        assert worker.site is None
        # result is initialized by parent class with initial structure
        assert "status" in worker.result
        assert worker.result["status"] == "pending"

    def test_get_job_type(self, mock_jobs_service):
        """Test get_job_type returns correct job type."""
        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        assert worker.get_job_type() == "add_svglanguages_template"

    def test_get_initial_result(self, mock_jobs_service):
        """Test get_initial_result returns correct structure."""
        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        result = worker.get_initial_result()

        assert result["status"] == "pending"
        assert "started_at" in result
        assert result["completed_at"] is None
        assert result["cancelled_at"] is None
        assert "summary" in result
        assert result["summary"]["total"] == 0
        assert result["summary"]["processed"] == 0
        assert result["summary"]["updated"] == 0
        assert result["summary"]["failed"] == 0
        assert result["summary"]["skipped"] == 0
        assert result["templates_processed"] == []


class TestLoadTemplates:
    """Tests for _load_templates and _apply_limits methods."""

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.template_service")
    def test_load_templates_filters_owid_templates(self, mock_template_service, mock_jobs_service):
        """Test that only OWID templates are loaded."""
        mock_templates = [
            MagicMock(id=1, title="Template:OWID/test1"),
            MagicMock(id=2, title="Template:OWID/test2"),
            MagicMock(id=3, title="Template:Other/not_owid"),
            MagicMock(id=4, title="Template:OWID/test3"),
        ]
        mock_template_service.list_templates.return_value = mock_templates

        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        templates = worker._load_templates()

        assert len(templates) == 3
        assert all(t.title.startswith("Template:OWID/") for t in templates)

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.template_service")
    def test_apply_limits_with_no_limit(self, mock_template_service, mock_jobs_service):
        """Test that all templates are returned when no limit is set."""
        mock_templates = [
            MagicMock(id=1, title="Template:OWID/test1"),
            MagicMock(id=2, title="Template:OWID/test2"),
        ]
        mock_template_service.list_templates.return_value = mock_templates

        with patch.object(settings.dynamic, "get", return_value=0):
            worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
            templates = worker._load_templates()

        assert len(templates) == 2

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.template_service")
    def test_apply_limits_applies_limit(self, mock_template_service, mock_jobs_service):
        """Test that limit is applied when configured."""
        mock_templates = [
            MagicMock(id=1, title="Template:OWID/test1"),
            MagicMock(id=2, title="Template:OWID/test2"),
            MagicMock(id=3, title="Template:OWID/test3"),
            MagicMock(id=4, title="Template:OWID/test4"),
            MagicMock(id=5, title="Template:OWID/test5"),
        ]
        mock_template_service.list_templates.return_value = mock_templates

        with patch.object(settings.dynamic, "get", return_value=3):
            worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
            templates = worker._load_templates()

        assert len(templates) == 3


class TestProcessTemplate:
    """Tests for _process_template method."""

    @pytest.fixture
    def mock_worker(self, mock_jobs_service):
        """Create a worker with mocked dependencies."""
        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        worker.site = MagicMock()
        worker.result = worker.get_initial_result()
        return worker

    def test_process_template_success_flow(self, mock_worker):
        """Test successful processing of a template."""
        template = MagicMock(id=1, title="Template:OWID/test")

        # Mock all steps to succeed
        mock_worker._step_load_template_text = MagicMock(return_value=True)
        mock_worker._step_generate_template_text = MagicMock(return_value=True)
        mock_worker._step_add_template = MagicMock(return_value=True)
        mock_worker._step_save_new_text = MagicMock(return_value=True)
        mock_worker._append = MagicMock()

        mock_worker._process_template(template)

        # Verify all steps were called
        mock_worker._step_load_template_text.assert_called_once()
        mock_worker._step_generate_template_text.assert_called_once()
        mock_worker._step_add_template.assert_called_once()
        mock_worker._step_save_new_text.assert_called_once()
        mock_worker._append.assert_called_once()

        # Verify summary was updated
        assert mock_worker.result["summary"]["processed"] == 1

    def test_process_template_load_step_fails(self, mock_worker):
        """Test that processing stops when load step fails."""
        template = MagicMock(id=1, title="Template:OWID/test")

        mock_worker._step_load_template_text = MagicMock(return_value=False)
        mock_worker._step_generate_template_text = MagicMock(return_value=True)
        mock_worker._step_add_template = MagicMock(return_value=True)
        mock_worker._step_save_new_text = MagicMock(return_value=True)
        mock_worker._append = MagicMock()

        mock_worker._process_template(template)

        # Only load step should be called
        mock_worker._step_load_template_text.assert_called_once()
        mock_worker._step_generate_template_text.assert_not_called()
        mock_worker._step_add_template.assert_not_called()
        mock_worker._step_save_new_text.assert_not_called()
        mock_worker._append.assert_called_once()

    def test_process_template_generate_step_fails(self, mock_worker):
        """Test that processing stops when generate step fails."""
        template = MagicMock(id=1, title="Template:OWID/test")

        mock_worker._step_load_template_text = MagicMock(return_value=True)
        mock_worker._step_generate_template_text = MagicMock(return_value=False)
        mock_worker._step_add_template = MagicMock(return_value=True)
        mock_worker._step_save_new_text = MagicMock(return_value=True)
        mock_worker._append = MagicMock()

        mock_worker._process_template(template)

        mock_worker._step_load_template_text.assert_called_once()
        mock_worker._step_generate_template_text.assert_called_once()
        mock_worker._step_add_template.assert_not_called()
        mock_worker._step_save_new_text.assert_not_called()


class TestStepLoadTemplateText:
    """Tests for _step_load_template_text method."""

    @pytest.fixture
    def mock_worker(self, mock_jobs_service):
        """Create a worker with mocked dependencies."""
        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        worker.site = MagicMock()
        worker.result = worker.get_initial_result()
        return worker

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.get_page_text")
    def test_load_template_text_success(self, mock_get_page_text, mock_worker):
        """Test successful loading of template text."""
        mock_get_page_text.return_value = "*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg"

        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        result = mock_worker._step_load_template_text(info)

        assert result is True
        assert info._text is not None
        assert info.steps["load_template_text"]["result"] is True

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.get_page_text")
    def test_load_template_text_returns_empty_string(self, mock_get_page_text, mock_worker):
        """Test failure when get_page_text returns empty string."""
        mock_get_page_text.return_value = ""

        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        result = mock_worker._step_load_template_text(info)

        assert result is False
        assert info.status == "failed"
        assert info.error is not None
        assert info.steps["load_template_text"]["result"] is False

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.get_page_text")
    def test_load_template_text_skips_if_already_has_svglanguages(self, mock_get_page_text, mock_worker):
        """Test that step is skipped if template already has SVGLanguages."""
        mock_get_page_text.return_value = "{{SVGLanguages|test.svg}}\nSome content"

        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        result = mock_worker._step_load_template_text(info)

        assert result is False
        assert info.steps["load_template_text"]["result"] is None  # Skipped
        assert "Skipped" in info.steps["load_template_text"]["msg"]


class TestStepGenerateTemplateText:
    """Tests for _step_generate_template_text method."""

    @pytest.fixture
    def mock_worker(self, mock_jobs_service):
        """Create a worker with mocked dependencies."""
        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        worker.site = MagicMock()
        worker.result = worker.get_initial_result()
        return worker

    def test_generate_template_text_success(self, mock_worker):
        """Test successful generation of template text."""
        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info._text = "*'''Translate''': https://svgtranslate.toolforge.org/File:test-file.svg"

        result = mock_worker._step_generate_template_text(info)

        assert result is True
        assert info._template_text == "{{SVGLanguages|test-file.svg}}"
        assert info.steps["generate_template_text"]["result"] is True

    def test_generate_template_text_no_translate_link(self, mock_worker):
        """Test failure when no Translate link is found."""
        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info._text = "Some content without translate link"

        result = mock_worker._step_generate_template_text(info)

        assert result is False
        assert info.status == "failed"
        assert "Could not load Translate link" in info.error


class TestStepAddTemplate:
    """Tests for _step_add_template method."""

    @pytest.fixture
    def mock_worker(self, mock_jobs_service):
        """Create a worker with mocked dependencies."""
        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        worker.site = MagicMock()
        worker.result = worker.get_initial_result()
        return worker

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.add_template_to_text")
    def test_add_template_success(self, mock_add_template, mock_worker):
        """Test successful addition of template to text."""
        mock_add_template.return_value = "original text\n*{{SVGLanguages|test.svg}}"

        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info._text = "original text"
        info._template_text = "{{SVGLanguages|test.svg}}"

        result = mock_worker._step_add_template(info)

        assert result is True
        assert info._new_text is not None
        mock_add_template.assert_called_once_with("original text", "{{SVGLanguages|test.svg}}")

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.add_template_to_text")
    def test_add_template_skips_if_identical(self, mock_add_template, mock_worker):
        """Test that step is skipped if new text is identical to original."""
        mock_add_template.return_value = "original text"

        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info._text = "original text"
        info._template_text = "{{SVGLanguages|test.svg}}"

        result = mock_worker._step_add_template(info)

        assert result is False
        assert info.status == "skipped"
        assert mock_worker.result["summary"]["skipped"] == 1
        assert mock_worker.result["summary"]["processed"] == 1


class TestStepSaveNewText:
    """Tests for _step_save_new_text method."""

    @pytest.fixture
    def mock_worker(self, mock_jobs_service):
        """Create a worker with mocked dependencies."""
        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        worker.site = MagicMock()
        worker.result = worker.get_initial_result()
        return worker

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.update_page_text")
    def test_save_new_text_success(self, mock_update_page_text, mock_worker):
        """Test successful saving of new text."""
        mock_update_page_text.return_value = {"success": True}

        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info._new_text = "updated text"
        info._template_text = "{{SVGLanguages|test.svg}}"

        result = mock_worker._step_save_new_text(info)

        assert result is True
        assert info.steps["save_new_text"]["result"] is True
        assert mock_worker.result["summary"]["updated"] == 1
        mock_update_page_text.assert_called_once()

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.update_page_text")
    def test_save_new_text_failure(self, mock_update_page_text, mock_worker):
        """Test failure when update_page_text fails."""
        mock_update_page_text.return_value = {"success": False, "error": "API error"}

        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info._new_text = "updated text"
        info._template_text = "{{SVGLanguages|test.svg}}"

        result = mock_worker._step_save_new_text(info)

        assert result is False
        assert info.status == "failed"
        assert info.error == "API error"
        assert info.steps["save_new_text"]["result"] is False


class TestHelperMethods:
    """Tests for helper methods _fail, _skip_step, _append."""

    @pytest.fixture
    def mock_worker(self, mock_jobs_service):
        """Create a worker with mocked dependencies."""
        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        worker.site = MagicMock()
        worker.result = worker.get_initial_result()
        return worker

    def test_fail_marks_step_and_file_as_failed(self, mock_worker):
        """Test that _fail correctly marks step and file as failed."""
        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")

        mock_worker._fail(info, "test_step", "Test error message")

        assert info.steps["test_step"]["result"] is False
        assert info.steps["test_step"]["msg"] == "Test error message"
        assert info.status == "failed"
        assert info.error == "Test error message"
        assert mock_worker.result["summary"]["failed"] == 1

    def test_skip_step_marks_step_as_skipped(self, mock_worker):
        """Test that _skip_step correctly marks step as skipped."""
        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")

        mock_worker._skip_step(info, "test_step", "Skip reason")

        assert info.steps["test_step"]["result"] is None
        assert info.steps["test_step"]["msg"] == "Skip reason"

    def test_append_adds_template_to_result(self, mock_worker):
        """Test that _append adds template info to result."""
        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info.status = "completed"

        mock_worker._append(info)

        assert len(mock_worker.result["templates_processed"]) == 1
        assert mock_worker.result["templates_processed"][0]["template_id"] == 1


class TestProcessMethod:
    """Tests for the main process() method."""

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.get_user_site")
    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.template_service")
    def test_process_success(self, mock_template_service, mock_get_user_site, mock_jobs_service):
        """Test successful processing of all templates."""
        mock_site = MagicMock()
        mock_get_user_site.return_value = mock_site

        mock_templates = [MagicMock(id=1, title="Template:OWID/test1")]
        mock_template_service.list_templates.return_value = mock_templates

        worker = AddSvgSVGLanguagesTemplate(job_id=1, user={"username": "test"})

        # Mock _process_template to do nothing
        worker._process_template = MagicMock()

        result = worker.process()

        assert result["status"] == "completed"
        assert result["summary"]["total"] == 1
        mock_get_user_site.assert_called_once()

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.get_user_site")
    def test_process_fails_without_site(self, mock_get_user_site, mock_jobs_service):
        """Test that process fails when site authentication is not available."""
        mock_get_user_site.return_value = None

        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        result = worker.process()

        assert result["status"] == "failed"
        assert "failed_at" in result

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.get_user_site")
    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.template_service")
    def test_process_handles_cancellation(self, mock_template_service, mock_get_user_site, mock_jobs_service):
        """Test that process stops when cancelled."""
        mock_site = MagicMock()
        mock_get_user_site.return_value = mock_site

        mock_templates = [
            MagicMock(id=1, title="Template:OWID/test1"),
            MagicMock(id=2, title="Template:OWID/test2"),
            MagicMock(id=3, title="Template:OWID/test3"),
        ]
        mock_template_service.list_templates.return_value = mock_templates

        cancel_event = threading.Event()
        worker = AddSvgSVGLanguagesTemplate(job_id=1, user={"username": "test"}, cancel_event=cancel_event)

        # Cancel after first template
        call_count = [0]

        def mock_process_template(template):
            call_count[0] += 1
            if call_count[0] == 1:
                cancel_event.set()

        worker._process_template = mock_process_template

        result = worker.process()

        # Should have processed only one template before cancellation
        assert call_count[0] == 1


class TestAddSvgSVGLanguagesTemplateToTemplates:
    """Tests for the add_svglanguages_template_to_templates function."""

    @patch("src.main_app.jobs_workers.add_svglanguages_template.worker.AddSvgSVGLanguagesTemplate")
    def test_function_creates_and_runs_worker(self, mock_worker_class, mock_jobs_service):
        """Test that the function creates and runs a worker."""
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance

        user = {"username": "test_user"}
        cancel_event = threading.Event()

        add_svglanguages_template_to_templates(job_id=1, user=user, cancel_event=cancel_event)

        mock_worker_class.assert_called_once_with(job_id=1, user=user, cancel_event=cancel_event)
        mock_worker_instance.run.assert_called_once()
