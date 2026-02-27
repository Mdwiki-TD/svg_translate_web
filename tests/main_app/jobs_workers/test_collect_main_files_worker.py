"""Unit tests for collect_main_files_worker module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers import collect_main_files_worker
from src.main_app.template_service import TemplateRecord


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    """Mock the services used by collect_main_files_worker."""

    # Mock get_templates_db_bg
    mock_templates_db_instance = MagicMock()
    mock_list_templates = MagicMock()
    mock_update_template = MagicMock()
    mock_templates_db_instance.list = mock_list_templates
    mock_templates_db_instance.update_if_not_none = mock_update_template
    monkeypatch.setattr(
        "src.main_app.jobs_workers.collect_main_files_worker.get_templates_db_bg",
        MagicMock(return_value=mock_templates_db_instance),
    )

    # Mock get_jobs_db_bg and save_job_result_by_name (imported in base_worker)
    mock_jobs_db_instance = MagicMock()
    mock_update_job_status = MagicMock()
    mock_jobs_db_instance.update_status = mock_update_job_status
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.get_jobs_db_bg",
        MagicMock(return_value=mock_jobs_db_instance),
    )

    mock_save_job_result = MagicMock(return_value="/tmp/job_1.json")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name", mock_save_job_result
    )

    # Mock get_wikitext
    mock_get_wikitext = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.collect_main_files_worker.get_wikitext", mock_get_wikitext)

    # Mock find_main_title
    mock_find_main_title = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.collect_main_files_worker.find_main_title", mock_find_main_title)

    return {
        "list_templates": mock_list_templates,
        "update_template": mock_update_template,
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "get_wikitext": mock_get_wikitext,
        "find_main_title": mock_find_main_title,
    }


def test_collect_main_files_with_no_templates(mock_services):
    """Test collect_main_files_for_templates when there are no templates."""
    mock_services["list_templates"].return_value = []

    collect_main_files_worker.collect_main_files_for_templates(1)

    # Should update status to running, then completed
    assert mock_services["update_job_status"].call_count == 2
    mock_services["update_job_status"].assert_any_call(
        1, "running", "collect_main_files_job_1.json", job_type="collect_main_files"
    )

    # Should save result
    mock_services["save_job_result_by_name"].assert_called_once()
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 0


def test_collect_main_files_skips_templates_with_main_file(mock_services):
    """Test that templates with main_file AND last_world_file are skipped."""
    templates = [
        TemplateRecord(id=1, title="Template:Test1", main_file="test1.svg", last_world_file="test1_2020.svg"),
        TemplateRecord(id=2, title="Template:Test2", main_file="test2.svg", last_world_file="test2_2020.svg"),
    ]
    mock_services["list_templates"].return_value = templates

    collect_main_files_worker.collect_main_files_for_templates(1)

    # Should not fetch wikitext for templates that have both main_file and last_world_file
    mock_services["get_wikitext"].assert_not_called()

    # Should save result with skipped templates
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 2
    assert result["summary"]["already_had_main_file"] == 2


def test_collect_main_files_updates_template_without_main_file(mock_services):
    """Test that templates without main_file are updated."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["get_wikitext"].return_value = "{{SVGLanguages|test.svg}}"
    mock_services["find_main_title"].return_value = "test.svg"

    collect_main_files_worker.collect_main_files_for_templates(1)

    # Should fetch wikitext
    mock_services["get_wikitext"].assert_called_once_with("Template:Test", project="commons.wikimedia.org")

    # Should find main title
    mock_services["find_main_title"].assert_called_once()

    # Should update template (using keyword arguments)
    mock_services["update_template"].assert_called_once_with(
        id=1, main_file="test.svg", last_world_file=None
    )

    # Should save result with updated template
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 1
    assert result["summary"]["updated"] == 1
    assert len(result["templates_updated"]) == 1
    assert result["templates_updated"][0]["new_main_file"] == "test.svg"


def test_collect_main_files_handles_missing_wikitext(mock_services):
    """Test that missing wikitext is handled gracefully."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["get_wikitext"].return_value = None

    collect_main_files_worker.collect_main_files_for_templates(1)

    # Should not try to find main title
    mock_services["find_main_title"].assert_not_called()

    # Should save result with failed template
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 1
    assert result["summary"]["failed"] == 1
    assert len(result["templates_failed"]) == 1
    assert "Could not fetch wikitext" in result["templates_failed"][0]["reason"]


def test_collect_main_files_handles_missing_main_title(mock_services):
    """Test that missing main title is handled gracefully."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["get_wikitext"].return_value = "some wikitext without SVGLanguages"
    mock_services["find_main_title"].return_value = None

    collect_main_files_worker.collect_main_files_for_templates(1)

    # Should not update template
    mock_services["update_template"].assert_not_called()

    # Should save result with failed template
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 1
    assert result["summary"]["failed"] == 1
    assert len(result["templates_failed"]) == 1
    assert "Could not find main file" in result["templates_failed"][0]["reason"]


def test_collect_main_files_handles_exception(mock_services):
    """Test that exceptions are handled gracefully."""
    templates = [
        TemplateRecord(id=1, title="Template:Test", main_file=None, last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates
    mock_services["get_wikitext"].side_effect = Exception("Network error")

    collect_main_files_worker.collect_main_files_for_templates(1)

    # Should save result with failed template
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 1
    assert result["summary"]["failed"] == 1
    assert len(result["templates_failed"]) == 1
    assert "Exception: Network error" in result["templates_failed"][0]["reason"]


def test_collect_main_files_processes_multiple_templates(mock_services):
    """Test processing multiple templates with mixed results."""
    templates = [
        TemplateRecord(id=1, title="Template:Test1", main_file=None, last_world_file=None),
        TemplateRecord(id=2, title="Template:Test2", main_file="already.svg", last_world_file=None),
        TemplateRecord(id=3, title="Template:Test3", main_file=None, last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates

    # First template: success
    # Third template: success
    def get_wikitext_side_effect(title, project):
        if "Test1" in title:
            return "{{SVGLanguages|test1.svg}}"
        elif "Test3" in title:
            return "{{SVGLanguages|test3.svg}}"
        return None

    def find_main_title_side_effect(wikitext):
        if "test1" in wikitext:
            return "test1.svg"
        elif "test3" in wikitext:
            return "test3.svg"
        return None

    mock_services["get_wikitext"].side_effect = get_wikitext_side_effect
    mock_services["find_main_title"].side_effect = find_main_title_side_effect

    collect_main_files_worker.collect_main_files_for_templates(1)

    # Should update two templates
    assert mock_services["update_template"].call_count == 2

    # Should save result with correct counts
    result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result["summary"]["total"] == 3
    assert result["summary"]["updated"] == 2
    assert result["summary"]["skipped"] == 0
