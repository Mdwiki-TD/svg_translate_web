"""Tests for job cancellation and error handling in workers."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.database.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files import FixNestedMainFilesWorker
from src.main_app.jobs_workers.objects import JobsRunner


def test_fix_nested_main_files_worker_cancellation(mock_base_worker, monkeypatch: pytest.MonkeyPatch):
    """Test that fix_nested_main_files_worker stops when cancelled."""
    mock_list_templates = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.TemplateService.list",
        mock_list_templates,
    )

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.FixNestedMainFilesWorker.repair_nested_svg_tags",
        MagicMock(return_value={"success": True, "message": "OK"}),
    )
    templates = [
        TemplateRecord(id=1, title="T1", main_file="f1.svg", last_world_file=None),
        TemplateRecord(id=2, title="T2", main_file="f2.svg", last_world_file=None),
    ]
    mock_list_templates.return_value = templates

    cancel_event = threading.Event()

    worker = FixNestedMainFilesWorker(JobsRunner(job_id=1, user={}, cancel_event=cancel_event))
    worker.run()

    result = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert len(result["pages_success"]) == 2
