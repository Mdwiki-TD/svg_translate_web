"""Unit tests for rename_owid_pages/worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.admin_jobs_workers.rename_owid_pages.runner import (
    rename_owid_pages_for_templates,
)

@pytest.fixture
def mock_worker_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = MagicMock()
    _mock_instance = MagicMock()
    _mock_class.return_value = _mock_instance
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.rename_owid_pages.runner.RenameOwidPagesWorker",
        _mock_class,
    )
    return _mock_class

class TestRenameOwidPagesForTemplatesEntryPoint:
    """Tests for the rename_owid_pages_for_templates entry point unified signature."""

    def test_entry_point_creates_and_runs_worker(self, mock_worker_class):
        rename_owid_pages_for_templates(job_id=1, user={"username": "tester"})

        mock_worker_class.assert_called_once_with(
            job_id=1,
            user={"username": "tester"},
            cancel_event=None,
        )
        mock_worker_class.return_value.run.assert_called_once()

    def test_entry_point_accepts_args_keyword_param(self, mock_worker_class):
        rename_owid_pages_for_templates(job_id=1, user=None, args={"some_key": "some_value"})

        mock_worker_class.return_value.run.assert_called_once()

    def test_entry_point_args_defaults_to_none(self, mock_worker_class):
        rename_owid_pages_for_templates(job_id=2, user=None)

        mock_worker_class.assert_called_once_with(
            job_id=2,
            user=None,
            cancel_event=None,
        )
        mock_worker_class.return_value.run.assert_called_once()

    def test_entry_point_with_cancel_event(self, mock_worker_class):
        cancel_event = threading.Event()
        rename_owid_pages_for_templates(job_id=3, user=None, cancel_event=cancel_event)

        mock_worker_class.assert_called_once_with(
            job_id=3,
            user=None,
            cancel_event=cancel_event,
        )
        mock_worker_class.return_value.run.assert_called_once()

    def test_entry_point_args_does_not_affect_worker_creation(self, mock_worker_class):
        rename_owid_pages_for_templates(job_id=4, user=None, args={"update_all": "true"})

        mock_worker_class.assert_called_once_with(
            job_id=4,
            user=None,
            cancel_event=None,
        )

