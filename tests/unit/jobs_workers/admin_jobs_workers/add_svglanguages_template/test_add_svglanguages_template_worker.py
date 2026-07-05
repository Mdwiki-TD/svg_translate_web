"""Unit tests for add_svglanguages_template worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.admin_jobs_workers.add_svglanguages_template.worker import (
    AddSvgSVGLanguagesTemplate,
    TemplateInfo,
)


@pytest.fixture
def mock_add_svg_worker(mock_base_worker, mock_before_run) -> AddSvgSVGLanguagesTemplate:
    worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
    worker.site = mock_base_worker["get_user_site"]
    return worker


# ── Test classes ─────────────────────────────────────────────────────────────


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

    def test_worker_initialization(self):
        """Test worker is initialized correctly."""
        user = {"username": "test_user"}
        cancel_event = threading.Event()

        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=user, cancel_event=cancel_event)

        assert worker.job_id == 1
        assert worker.user == user
        assert worker.cancel_event == cancel_event
        assert worker.site is None
        assert worker.result.status == "pending"

    def test_worker_reads_limit_items_from_args(self):
        """Test worker reads limit_items from args."""
        worker = AddSvgSVGLanguagesTemplate(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"limit_items": 10},
        )

        assert worker.limit_items == 10

    def test_worker_defaults_limit_items_when_args_none(self):
        """Test worker defaults limit_items to 0 when args is None."""
        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None, cancel_event=None, args=None)

        assert worker.limit_items == 0

    def test_worker_limit_items_none_when_key_missing(self):
        """Test worker sets limit_items to 0 when args has no limit_items key."""
        worker = AddSvgSVGLanguagesTemplate(
            job_id=1,
            user=None,
            cancel_event=None,
            args={"other_key": "value"},
        )

        assert worker.limit_items == 0

    def test_get_job_type(self):
        """Test get_job_type returns correct job type."""
        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        assert worker.get_job_type() == "add_svglanguages_template"

    def test_get_initial_result(self):
        """Test initial result structure."""
        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        result = worker.result

        assert result.status == "pending"
        assert result.started_at is not None
        assert result.completed_at is None
        assert result.cancelled_at is None
        assert result.summary.total == 0
        assert result.summary.processed == 0
        assert result.summary.success == 0
        assert result.summary.failed == 0
        assert result.summary.skipped == 0
        assert result.pages_processed == []


class TestLoadTemplates:
    """Tests for _load_templates and _apply_limits methods."""

    def test_load_templates_filters_owid_templates(self, mock_add_svglanguages_services):
        """Test that only OWID templates are loaded."""
        mock_templates = [
            MagicMock(id=1, title="Template:OWID/test1"),
            MagicMock(id=2, title="Template:OWID/test2"),
            MagicMock(id=3, title="Template:Other/not_owid"),
            MagicMock(id=4, title="Template:OWID/test3"),
        ]
        mock_add_svglanguages_services["list_templates"].return_value = mock_templates

        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        templates = worker._load_templates()

        assert len(templates) == 3
        assert all(t.title.startswith("Template:OWID/") for t in templates)


class TestProcessTemplate:
    """Tests for _process_one_item method."""

    def test_process_one_success_flow(self, mock_add_svglanguages_services, mock_add_svg_worker):
        """Test successful processing of a template."""
        template = MagicMock(id=1, title="Template:OWID/test")

        # Mock regex to not match (template doesn't have SVGLanguages yet)
        mock_add_svglanguages_services["RE_SVG_LANG"].search = MagicMock(return_value=None)

        # Mock all steps to succeed, with side_effects to set required state
        def mock_load(info, page):
            info._text = "some text"
            return True

        def mock_generate(info):
            info._template_text = "{{SVGLanguages|test.svg}}"
            return True

        def mock_add(info):
            info._new_text = "updated text"
            return True

        mock_add_svg_worker._step_load_template_text = MagicMock(side_effect=mock_load)
        mock_add_svg_worker._step_generate_template_text = MagicMock(side_effect=mock_generate)
        mock_add_svg_worker._step_add_template = MagicMock(side_effect=mock_add)
        mock_add_svg_worker._step_save_new_text = MagicMock(return_value=True)

        mock_add_svg_worker._process_one_item(template)

        # Verify all steps were called
        mock_add_svg_worker._step_load_template_text.assert_called_once()
        mock_add_svg_worker._step_generate_template_text.assert_called_once()
        mock_add_svg_worker._step_add_template.assert_called_once()
        mock_add_svg_worker._step_save_new_text.assert_called_once()

        # Verify summary was updated
        assert mock_add_svg_worker.result.summary.processed == 1

    def test_process_one_load_step_fails(self, mock_add_svg_worker):
        """Test that processing stops when load step fails."""
        template = MagicMock(id=1, title="Template:OWID/test")

        mock_add_svg_worker._step_load_template_text = MagicMock(return_value=False)
        mock_add_svg_worker._step_generate_template_text = MagicMock()
        mock_add_svg_worker._step_add_template = MagicMock()
        mock_add_svg_worker._step_save_new_text = MagicMock()

        mock_add_svg_worker._process_one_item(template)

        # Only load step should be called
        mock_add_svg_worker._step_load_template_text.assert_called_once()
        mock_add_svg_worker._step_generate_template_text.assert_not_called()
        mock_add_svg_worker._step_add_template.assert_not_called()
        mock_add_svg_worker._step_save_new_text.assert_not_called()

    def test_process_one_generate_step_fails(self, mock_add_svglanguages_services, mock_add_svg_worker):
        """Test that processing stops when generate step fails."""
        template = MagicMock(id=1, title="Template:OWID/test")

        # Mock regex to not match (so it proceeds past the skip check)
        mock_add_svglanguages_services["RE_SVG_LANG"].search = MagicMock(return_value=None)

        def mock_load(info, page):
            info._text = "some text"
            return True

        mock_add_svg_worker._step_load_template_text = MagicMock(side_effect=mock_load)
        mock_add_svg_worker._step_generate_template_text = MagicMock(return_value=False)
        mock_add_svg_worker._step_add_template = MagicMock()
        mock_add_svg_worker._step_save_new_text = MagicMock()

        mock_add_svg_worker._process_one_item(template)

        mock_add_svg_worker._step_load_template_text.assert_called_once()
        mock_add_svg_worker._step_generate_template_text.assert_called_once()
        mock_add_svg_worker._step_add_template.assert_not_called()
        mock_add_svg_worker._step_save_new_text.assert_not_called()


class TestStepLoadTemplateText:
    """Tests for _step_load_template_text method."""

    def test_load_template_text_success(self, mock_add_svglanguages_services, mock_add_svg_worker):
        """Test successful loading of template text."""
        mock_page = MagicMock()
        mock_page.get_text.return_value = "*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg"

        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        result = mock_add_svg_worker._step_load_template_text(info, mock_page)

        assert result is True
        assert info._text is not None
        assert info.steps["load_template_text"]["result"] is True

    def test_load_template_text_returns_empty_string(self, mock_add_svglanguages_services, mock_add_svg_worker):
        """Test failure when get_page_text returns empty string."""
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""

        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        result = mock_add_svg_worker._step_load_template_text(info, mock_page)

        assert result is False
        assert info.status == "failed"
        assert info.error is not None
        assert info.steps["load_template_text"]["result"] is False

    def test_load_template_text_skips_if_already_has_svglanguages(
        self, mock_add_svglanguages_services, mock_add_svg_worker
    ):
        """Test that _process_one_item skips if template already has SVGLanguages."""
        template = MagicMock(id=1, title="Template:OWID/test")

        # Mock regex to match (template already has SVGLanguages)
        mock_match = MagicMock()
        mock_add_svglanguages_services["RE_SVG_LANG"].search = MagicMock(return_value=mock_match)

        def mock_load(info, page):
            info._text = "{{SVGLanguages|test.svg}}\nSome content"
            return True

        mock_add_svg_worker._step_load_template_text = MagicMock(side_effect=mock_load)
        mock_add_svg_worker._step_generate_template_text = MagicMock()
        mock_add_svg_worker._step_add_template = MagicMock()
        mock_add_svg_worker._step_save_new_text = MagicMock()

        mock_add_svg_worker._skip_step = MagicMock()

        result = mock_add_svg_worker._process_one_item(template)

        assert result is False
        mock_add_svg_worker._step_load_template_text.assert_called_once()
        mock_add_svg_worker._step_generate_template_text.assert_not_called()
        # mock_worker._skip_step.assert_called_once()


class TestStepGenerateTemplateText:
    """Tests for _step_generate_template_text method."""

    def test_generate_template_text_success(self, mock_add_svg_worker):
        """Test successful generation of template text."""
        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info._text = "*'''Translate''': https://svgtranslate.toolforge.org/File:test-file.svg"

        result = mock_add_svg_worker._step_generate_template_text(info)

        assert result is True
        assert info._template_text == "{{SVGLanguages|test-file.svg}}"
        assert info.steps["generate_template_text"]["result"] is True

    def test_generate_template_text_no_translate_link(self, mock_add_svg_worker):
        """Test failure when no Translate link is found."""
        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info._text = "Some content without translate link"

        result = mock_add_svg_worker._step_generate_template_text(info)

        assert result is False
        assert info.status == "failed"
        assert "Could not load svgtranslate link" in info.error


class TestStepAddTemplate:
    """Tests for _step_add_template method."""

    def test_add_template_success(self, mock_add_svglanguages_services, mock_add_svg_worker):
        """Test successful addition of template to text."""
        mock_add_svglanguages_services["add_template_to_text"].return_value = (
            "original text\n*{{SVGLanguages|test.svg}}"
        )

        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info._text = "original text"
        info._template_text = "{{SVGLanguages|test.svg}}"

        result = mock_add_svg_worker._step_add_template(info)

        assert result is True
        assert info._new_text is not None
        mock_add_svglanguages_services["add_template_to_text"].assert_called_once_with(
            "original text", "{{SVGLanguages|test.svg}}"
        )

    def test_add_template_skips_if_identical(self, mock_add_svglanguages_services, mock_add_svg_worker):
        """Test that step is skipped if new text is identical to original."""
        mock_add_svglanguages_services["add_template_to_text"].return_value = "original text"

        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info._text = "original text"
        info._template_text = "{{SVGLanguages|test.svg}}"

        result = mock_add_svg_worker._step_add_template(info)

        assert result is False
        assert info.status == "skipped"
        assert info.steps["add_template_text"]["result"] is None


class TestStepSaveNewText:
    """Tests for _step_save_new_text method."""

    def test_save_new_text_success(self, mock_add_svglanguages_services, mock_add_svg_worker):
        """Test successful saving of new text."""
        mock_page = MagicMock()
        mock_page.edit.return_value = {"success": True}

        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info._new_text = "updated text"
        info._template_text = "{{SVGLanguages|test.svg}}"

        result = mock_add_svg_worker._step_save_new_text(info, mock_page)

        assert result is True
        assert info.steps["save_new_text"]["result"] is True
        mock_page.edit.assert_called_once()

    def test_save_new_text_failure(self, mock_add_svglanguages_services, mock_add_svg_worker):
        """Test failure when edit fails."""
        mock_page = MagicMock()
        mock_page.edit.return_value = {"success": False, "error": "API error"}

        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")
        info._new_text = "updated text"
        info._template_text = "{{SVGLanguages|test.svg}}"

        result = mock_add_svg_worker._step_save_new_text(info, mock_page)

        assert result is False
        assert info.status == "failed"
        assert info.error == "API error"
        assert info.steps["save_new_text"]["result"] is False


class TestHelperMethods:
    """Tests for helper methods _fail, _skip_step."""

    def test_fail_marks_step_and_file_as_failed(self, mock_add_svg_worker):
        """Test that _fail correctly marks step and file as failed."""
        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")

        mock_add_svg_worker._fail(info, "test_step", "Test error message")

        assert info.steps["test_step"]["result"] is False
        assert info.steps["test_step"]["msg"] == "Test error message"
        assert info.status == "failed"
        assert info.error == "Test error message"

    def test_skip_step_marks_step_as_skipped(self, mock_add_svg_worker):
        """Test that _skip_step correctly marks step as skipped."""
        info = TemplateInfo(template_id=1, template_title="Template:OWID/test")

        mock_add_svg_worker._skip_step(info, "test_step", "Skip reason")

        assert info.steps["test_step"]["result"] is None
        assert info.steps["test_step"]["msg"] == "Skip reason"


class TestProcessMethod:
    """Tests for the main process() method."""

    def test_process_success(self, mock_add_svglanguages_services, mock_site, monkeypatch: pytest.MonkeyPatch):
        """Test successful processing of all templates."""
        mock_add_svglanguages_services["get_user_site"].return_value = mock_site

        mock_templates = [MagicMock(id=1, title="Template:OWID/test1")]
        mock_add_svglanguages_services["list_templates"].return_value = mock_templates

        worker = AddSvgSVGLanguagesTemplate(job_id=1, user={"username": "test"})

        # Mock _process_one_item to do nothing
        worker._process_one_item = MagicMock()

        result = worker.run()

        assert result["status"] == "completed"
        assert result["summary"]["total"] == 1
        mock_add_svglanguages_services["get_user_site"].assert_called_once()

    def test_process_fails_without_site(self, mock_add_svglanguages_services, monkeypatch: pytest.MonkeyPatch):
        """Test that process fails when site authentication is not available."""
        mock_add_svglanguages_services["get_user_site"].return_value = None

        worker = AddSvgSVGLanguagesTemplate(job_id=1, user=None)
        result = worker.run()

        assert result["status"] == "failed"
        assert result["failed_at"] is not None

    def test_process_handles_cancellation(
        self, mock_add_svglanguages_services, mock_site, monkeypatch: pytest.MonkeyPatch
    ):
        """Test that process stops when cancelled."""
        mock_add_svglanguages_services["get_user_site"].return_value = mock_site

        mock_templates = [
            MagicMock(id=1, title="Template:OWID/test1"),
            MagicMock(id=2, title="Template:OWID/test2"),
            MagicMock(id=3, title="Template:OWID/test3"),
        ]
        mock_add_svglanguages_services["list_templates"].return_value = mock_templates

        cancel_event = threading.Event()
        worker = AddSvgSVGLanguagesTemplate(job_id=1, user={"username": "test"}, cancel_event=cancel_event)

        # Cancel after first template
        call_count = [0]

        def mock_process_one(template):
            call_count[0] += 1
            if call_count[0] == 1:
                cancel_event.set()

        worker._process_one_item = mock_process_one  # type: ignore

        _result = worker.process()

        # Should have processed only one template before cancellation
        assert call_count[0] == 1
