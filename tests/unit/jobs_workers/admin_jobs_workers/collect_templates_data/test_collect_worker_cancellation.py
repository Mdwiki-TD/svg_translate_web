"""Tests for job cancellation and error handling in workers."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data import worker as collect_worker




@pytest.fixture(autouse=True)
def mock_services(monkeypatch: pytest.MonkeyPatch):
    """Mock services common to both workers."""

    cancel_event = threading.Event()
    mocks = {
        "cancel_event": cancel_event,
        "list_templates": MagicMock(),
    }
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.list_templates",
        mocks["list_templates"],
    )
    # Mock update_template_data to set the cancel event
    mock_update_template = MagicMock()

    # Should have processed only one template before stopping
    # n=1: processes T1, updates template, sets cancel_event.
    # n=2: checks cancel_event.is_set() -> True. Breaks.

    def side_effect(*args, **kwargs):
        cancel_event.set()

    mock_update_template.side_effect = side_effect

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.MwClientPage",
        lambda title, site: MagicMock(get_text=MagicMock(return_value="some wikitext")),
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_main_title",
        lambda x: "file.svg",
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_newest_world_file",
        lambda x: None,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.update_template_data",
        mock_update_template,
    )
    # Mock get_category_members to return empty list (no new templates to add)
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.get_category_members",
        MagicMock(return_value=[]),
    )

    # Mock add_template_data to avoid database calls
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.add_template_data",
        MagicMock(),
    )

    return mocks

def test_collect_templates_data_worker_cancellation(mock_services, mock_base_worker_object):
    """Test that collect_templates_data_worker stops when cancelled."""
    templates = [
        TemplateRecord(id=1, title="T1", main_file=None, last_world_file=None),
        TemplateRecord(id=2, title="T2", main_file=None, last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates

    collect_worker.collect_templates_data_entry(job_id=1, user=None, cancel_event=mock_services["cancel_event"])

    result = mock_base_worker_object["save_job_result_by_name"].call_args[0][1]
    assert result.get("status") == "cancelled"
    assert len(result["pages_updated"]) == 1
