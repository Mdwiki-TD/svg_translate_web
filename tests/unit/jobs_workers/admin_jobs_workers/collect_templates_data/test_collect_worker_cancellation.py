"""Tests for job cancellation and error handling in workers."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data import runner as collect_runner


@pytest.fixture(autouse=True)
def mock_services(monkeypatch: pytest.MonkeyPatch):
    """Mock services common to both workers."""

    cancel_event = threading.Event()
    mocks = {
        "cancel_event": cancel_event,
        "list_templates": MagicMock(),
    }

    # Mock update_template_data to set the cancel event
    mock_update_template = MagicMock()

    def side_effect(*args, **kwargs):
        cancel_event.set()

    mock_update_template.side_effect = side_effect

    mock_template_service = MagicMock()
    mock_template_service.list_templates = mocks["list_templates"]
    mock_template_service.add_template_data = MagicMock()
    mock_template_service.update_template_data = mock_update_template
    mock_template_service.get_template_by_title = MagicMock()

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.TemplateService",
        MagicMock(return_value=mock_template_service),
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.MwClientPage",
        lambda title, site: MagicMock(get_text=MagicMock(return_value="some wikitext")),
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_main_title",
        lambda x, remove_prefix=False: "file.svg",
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.find_newest_world_file",
        lambda x, remove_prefix=False: None,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data.worker.get_category_members",
        MagicMock(return_value=[]),
    )

    return mocks


def test_collect_templates_data_worker_cancellation(mock_services, mock_base_worker):
    """Test that collect_templates_data_worker stops when cancelled."""
    templates = [
        TemplateRecord(id=1, title="T1", main_file=None, last_world_file=None),
        TemplateRecord(id=2, title="T2", main_file=None, last_world_file=None),
    ]
    mock_services["list_templates"].return_value = templates

    collect_runner.collect_templates_data_entry(job_id=1, user=None, cancel_event=mock_services["cancel_event"])

    result = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert result.get("status") == "cancelled"
    assert len(result["pages_updated"]) == 1
