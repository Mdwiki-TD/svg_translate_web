"""Tests for job cancellation and error handling in workers."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers import collect_main_files_worker, fix_nested_main_files_worker
from src.main_app.template_service import TemplateRecord


@pytest.fixture
def mock_common_services(monkeypatch: pytest.MonkeyPatch):
    """Mock services common to both workers."""
    mock_list_templates = MagicMock()
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock()
    mock_generate_result_file_name = MagicMock(return_value="result.json")

    # Mock for collect_main_files_worker
    monkeypatch.setattr(
        "src.main_app.jobs_workers.collect_main_files_worker.template_service.list_templates", mock_list_templates
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.collect_main_files_worker.jobs_service.update_job_status", mock_update_job_status
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.collect_main_files_worker.jobs_service.save_job_result_by_name", mock_save_job_result
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.collect_main_files_worker.generate_result_file_name",
        mock_generate_result_file_name,
    )

    # Mock for fix_nested_main_files_worker
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.template_service.list_templates", mock_list_templates
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.jobs_service.update_job_status", mock_update_job_status
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.jobs_service.save_job_result_by_name",
        mock_save_job_result,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.generate_result_file_name",
        mock_generate_result_file_name,
    )

    return {
        "list_templates": mock_list_templates,
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
    }


def test_collect_main_files_worker_cancellation(mock_common_services, monkeypatch: pytest.MonkeyPatch):
    """Test that collect_main_files_worker stops when cancelled."""
    templates = [
        TemplateRecord(id=1, title="T1", main_file=None, last_world_file=None),
        TemplateRecord(id=2, title="T2", main_file=None, last_world_file=None),
    ]
    mock_common_services["list_templates"].return_value = templates

    # Mock update_template_if_not_none to set the cancel event
    cancel_event = threading.Event()
    mock_update_template = MagicMock()

    def side_effect(*args, **kwargs):
        cancel_event.set()

    mock_update_template.side_effect = side_effect

    monkeypatch.setattr(
        "src.main_app.jobs_workers.collect_main_files_worker.get_wikitext", lambda t, **kwargs: "some wikitext"
    )
    monkeypatch.setattr("src.main_app.jobs_workers.collect_main_files_worker.find_main_title", lambda x: "file.svg")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.collect_main_files_worker.find_last_world_file_from_owidslidersrcs", lambda x: None
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.collect_main_files_worker.template_service.update_template_if_not_none",
        mock_update_template,
    )

    collect_main_files_worker.collect_main_files_for_templates(1, cancel_event=cancel_event)

    # Should have processed only one template before stopping
    # n=1: processes T1, updates template, sets cancel_event.
    # n=2: checks cancel_event.is_set() -> True. Breaks.

    result = mock_common_services["save_job_result_by_name"].call_args[0][1]
    assert result.get("status") == "cancelled"
    assert result["summary"]["updated"] == 1


def test_fix_nested_main_files_worker_cancellation(mock_common_services, monkeypatch: pytest.MonkeyPatch):
    """Test that fix_nested_main_files_worker stops when cancelled."""
    templates = [
        TemplateRecord(id=1, title="T1", main_file="f1.svg", last_world_file=None),
        TemplateRecord(id=2, title="T2", main_file="f2.svg", last_world_file=None),
    ]
    mock_common_services["list_templates"].return_value = templates

    cancel_event = threading.Event()

    def mock_repair_nested_svg_tags(filename, user, cancel_event=None):
        cancel_event.set()
        return {"success": True, "message": "OK"}

    monkeypatch.setattr(
        "src.main_app.jobs_workers.fix_nested_main_files_worker.repair_nested_svg_tags", mock_repair_nested_svg_tags
    )

    fix_nested_main_files_worker.fix_nested_main_files_for_templates(1, user=None, cancel_event=cancel_event)

    result = mock_common_services["save_job_result_by_name"].call_args[0][1]
    assert result["status"] == "cancelled"
    assert result["summary"]["success"] == 1


def test_worker_handles_deleted_job(mock_common_services, monkeypatch: pytest.MonkeyPatch):
    """Test that workers handle LookupError when the job record is deleted."""
    mock_common_services["list_templates"].return_value = []
    # Force LookupError on status update
    mock_common_services["update_job_status"].side_effect = LookupError("Job not found")

    # Should not raise exception
    collect_main_files_worker.collect_main_files_for_templates(1)
    fix_nested_main_files_worker.fix_nested_main_files_for_templates(2, user=None)

    assert mock_common_services["update_job_status"].call_count >= 2
