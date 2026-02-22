"""Unit tests for fix_nested_main_files_worker module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers import fix_nested_main_files_worker
from src.main_app.template_service import TemplateRecord


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    """Mock the services used by fix_nested_main_files_worker."""

    # Mock template_service
    mock_list_templates = MagicMock()
    mock_update_template = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.template_service.list_templates", mock_list_templates
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.template_service.update_template", mock_update_template
    )

    # Mock jobs_service
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock(return_value="/tmp/job_1.json")
    mock_generate_result_file_name = MagicMock(side_effect=lambda job_id, job_type: f"{job_type}_job_{job_id}.json")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.jobs_service.update_job_status", mock_update_job_status
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.jobs_service.save_job_result_by_name", mock_save_job_result
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.jobs_service.generate_result_file_name",
        mock_generate_result_file_name,
    )

    # Mock get_wikitext
    mock_get_wikitext = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.fix_nested_main_files_worker.get_wikitext", mock_get_wikitext)

    # Mock find_main_title
    mock_find_main_title = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.fix_nested_main_files_worker.find_main_title", mock_find_main_title)

    return {
        "list_templates": mock_list_templates,
        "update_template": mock_update_template,
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "generate_result_file_name": mock_generate_result_file_name,
        "get_wikitext": mock_get_wikitext,
        "find_main_title": mock_find_main_title,
    }


@pytest.fixture
def mock_fix_nested_services(monkeypatch: pytest.MonkeyPatch):
    """Mock the services used by fix_nested_main_files_for_templates."""
    # Mock template_service
    mock_list_templates = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.template_service.list_templates", mock_list_templates
    )

    # Mock jobs_service
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock(return_value="/tmp/job_1.json")
    mock_generate_result_file_name = MagicMock(side_effect=lambda job_id, job_type: f"{job_type}_job_{job_id}.json")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.jobs_service.update_job_status", mock_update_job_status
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.jobs_service.save_job_result_by_name", mock_save_job_result
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.jobs_service.generate_result_file_name",
        mock_generate_result_file_name,
    )

    # Mock repair_nested_svg_tags
    mock_process_fix_nested = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.repair_nested_svg_tags", mock_process_fix_nested
    )

    return {
        "list_templates": mock_list_templates,
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "generate_result_file_name": mock_generate_result_file_name,
        "repair_nested_svg_tags": mock_process_fix_nested,
    }


def test_fix_nested_main_files_with_no_templates(mock_fix_nested_services):
    """Test fix_nested_main_files_for_templates when there are no templates."""
    mock_fix_nested_services["list_templates"].return_value = []

    user = {"username": "test_user"}
    fix_nested_main_files_worker.fix_nested_main_files_for_templates(700, user)

    # Should update status to running, then completed
    assert mock_fix_nested_services["update_job_status"].call_count == 2
    mock_fix_nested_services["update_job_status"].assert_any_call(
        700, "running", "fix_nested_main_files_job_700.json", job_type="fix_nested_main_files"
    )

    # Should save result
    mock_fix_nested_services["save_job_result_by_name"].assert_called_once()
    result = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 0


def test_fix_nested_main_files_skips_templates_without_main_file(mock_fix_nested_services):
    """Test that templates without main_file are skipped."""
    templates = [
        TemplateRecord(id=1, title="Template:Test1", main_file=None),
        TemplateRecord(id=2, title="Template:Test2", main_file=None),
    ]
    mock_fix_nested_services["list_templates"].return_value = templates

    user = {"username": "test_user"}
    fix_nested_main_files_worker.fix_nested_main_files_for_templates(1, user)

    # Should not call repair_nested_svg_tags
    mock_fix_nested_services["repair_nested_svg_tags"].assert_not_called()

    # Should save result with skipped templates
    result = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 2
    assert result["summary"]["skipped"] == 2
    assert result["summary"]["no_main_file"] == 2


def test_fix_nested_main_files_processes_template_with_main_file(mock_fix_nested_services):
    """Test that templates with main_file are processed."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file="test.svg"),
    ]
    mock_fix_nested_services["list_templates"].return_value = templates
    mock_fix_nested_services["repair_nested_svg_tags"].return_value = {
        "success": True,
        "message": "Successfully fixed 2 nested tag(s) and uploaded test.svg.",
    }

    user = {"username": "test_user"}
    fix_nested_main_files_worker.fix_nested_main_files_for_templates(1, user)

    # Should call repair_nested_svg_tags
    mock_fix_nested_services["repair_nested_svg_tags"].assert_called_once_with(
        filename="test.svg",
        user=user,
        cancel_event=None,
    )

    # Should save result with successful template
    result = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 1
    assert result["summary"]["success"] == 1
    assert len(result["templates_success"]) == 1
    assert result["templates_success"][0]["main_file"] == "test.svg"


def test_fix_nested_main_files_handles_failed_fix(mock_fix_nested_services):
    """Test that failed fixes are handled gracefully."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file="test.svg"),
    ]
    mock_fix_nested_services["list_templates"].return_value = templates
    mock_fix_nested_services["repair_nested_svg_tags"].return_value = {
        "success": False,
        "message": "No nested tags found",
        "no_nested_tags": True,
    }

    user = {"username": "test_user"}
    fix_nested_main_files_worker.fix_nested_main_files_for_templates(1, user)

    # Should save result with failed template
    result = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 1
    assert result["summary"]["failed"] == 0
    assert result["summary"]["skipped"] == 1
    assert len(result["templates_skipped"]) == 1
    assert "No nested tags found" in result["templates_skipped"][0]["reason"]


def test_fix_nested_main_files_handles_exception(mock_fix_nested_services):
    """Test that exceptions are handled gracefully."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file="test.svg"),
    ]
    mock_fix_nested_services["list_templates"].return_value = templates
    mock_fix_nested_services["repair_nested_svg_tags"].side_effect = Exception("Network error")

    user = {"username": "test_user"}
    fix_nested_main_files_worker.fix_nested_main_files_for_templates(1, user)

    # Should save result with failed template
    result = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 1
    assert result["summary"]["failed"] == 1
    assert len(result["templates_failed"]) == 1
    assert "Exception: Network error" in result["templates_failed"][0]["reason"]


def test_fix_nested_main_files_processes_multiple_templates(mock_fix_nested_services):
    """Test processing multiple templates with mixed results."""
    templates = [
        TemplateRecord(id=1, title="Template:Test1", main_file="test1.svg"),
        TemplateRecord(id=2, title="Template:Test2", main_file=None),
        TemplateRecord(id=3, title="Template:Test3", main_file="test3.svg"),
    ]
    mock_fix_nested_services["list_templates"].return_value = templates

    # First template: success, third template: success
    def process_fix_nested_side_effect(filename, user, cancel_event=None):
        if "test1" in filename:
            return {"success": True, "message": "Fixed test1.svg"}
        elif "test3" in filename:
            return {"success": True, "message": "Fixed test3.svg"}
        return {"success": False, "message": "Failed"}

    mock_fix_nested_services["repair_nested_svg_tags"].side_effect = process_fix_nested_side_effect

    user = {"username": "test_user"}
    fix_nested_main_files_worker.fix_nested_main_files_for_templates(1, user)

    # Should process two templates
    assert mock_fix_nested_services["repair_nested_svg_tags"].call_count == 2

    # Should save result with correct counts
    result = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 3
    assert result["summary"]["success"] == 2
    assert result["summary"]["skipped"] == 1
    assert result["summary"]["no_main_file"] == 1
