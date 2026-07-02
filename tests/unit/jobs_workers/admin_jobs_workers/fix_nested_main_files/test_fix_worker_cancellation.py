"""Tests for job cancellation and error handling in workers."""

from __future__ import annotations

import threading
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files import worker as fix_worker





def test_fix_nested_main_files_worker_cancellation(mock_base_worker_object, monkeypatch: pytest.MonkeyPatch):
    """Test that fix_nested_main_files_worker stops when cancelled."""
    mock_list_templates = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.list_templates",
        mock_list_templates,
    )
    def mock_repair_nested_svg_tags(
        filename,
        site,
        temp_dir,
    ) -> dict[str, Any]:
        return {"success": True, "message": "OK"}

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.repair_nested_svg_tags",
        mock_repair_nested_svg_tags,
    )
    templates = [
        TemplateRecord(id=1, title="T1", main_file="f1.svg", last_world_file=None),
        TemplateRecord(id=2, title="T2", main_file="f2.svg", last_world_file=None),
    ]
    mock_list_templates.return_value = templates

    cancel_event = threading.Event()

    fix_worker.fix_nested_main_files_for_templates(job_id=1, user=None, cancel_event=cancel_event)

    result = mock_base_worker_object["save_job_result_by_name"].call_args[0][1]
    assert len(result["pages_success"]) == 2
