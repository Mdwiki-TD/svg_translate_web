"""Unit tests for rename_owid_pages/worker module (entry point signature changes)."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

from src.main_app.jobs_workers.rename_owid_pages.worker import (
    RenameOwidPagesWorker,
    rename_owid_pages_for_templates,
)


class TestRenameOwidPagesForTemplatesEntryPoint:
    """Tests for the rename_owid_pages_for_templates entry point unified signature."""

    @patch("src.main_app.jobs_workers.rename_owid_pages.worker.RenameOwidPagesWorker")
    def test_entry_point_creates_and_runs_worker(self, mock_worker_class, mock_jobs_service):
        """Test that the entry point creates a RenameOwidPagesWorker and calls run()."""
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance

        rename_owid_pages_for_templates(job_id=1, user={"username": "tester"})

        mock_worker_class.assert_called_once_with(
            job_id=1,
            user={"username": "tester"},
            cancel_event=None,
        )
        mock_worker_instance.run.assert_called_once()

    @patch("src.main_app.jobs_workers.rename_owid_pages.worker.RenameOwidPagesWorker")
    def test_entry_point_accepts_args_keyword_param(self, mock_worker_class, mock_jobs_service):
        """Test that rename_owid_pages_for_templates accepts args= keyword-only param (unified signature)."""
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance

        # Should not raise TypeError; args is accepted but unused
        rename_owid_pages_for_templates(job_id=1, user=None, args={"some_key": "some_value"})

        mock_worker_instance.run.assert_called_once()

    @patch("src.main_app.jobs_workers.rename_owid_pages.worker.RenameOwidPagesWorker")
    def test_entry_point_args_defaults_to_none(self, mock_worker_class, mock_jobs_service):
        """Test that args defaults to None and entry point works without it."""
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance

        # Call without args param - should use None default
        rename_owid_pages_for_templates(job_id=2, user=None)

        mock_worker_class.assert_called_once_with(
            job_id=2,
            user=None,
            cancel_event=None,
        )
        mock_worker_instance.run.assert_called_once()

    @patch("src.main_app.jobs_workers.rename_owid_pages.worker.RenameOwidPagesWorker")
    def test_entry_point_with_cancel_event(self, mock_worker_class, mock_jobs_service):
        """Test that cancel_event is passed correctly (keyword-only)."""
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance

        cancel_event = threading.Event()
        rename_owid_pages_for_templates(job_id=3, user=None, cancel_event=cancel_event)

        mock_worker_class.assert_called_once_with(
            job_id=3,
            user=None,
            cancel_event=cancel_event,
        )
        mock_worker_instance.run.assert_called_once()

    @patch("src.main_app.jobs_workers.rename_owid_pages.worker.RenameOwidPagesWorker")
    def test_entry_point_args_does_not_affect_worker_creation(self, mock_worker_class, mock_jobs_service):
        """Test that args is not forwarded to RenameOwidPagesWorker (it's unused)."""
        mock_worker_instance = MagicMock()
        mock_worker_class.return_value = mock_worker_instance

        rename_owid_pages_for_templates(job_id=4, user=None, args={"update_all": "true"})

        # Worker should be created WITHOUT args (it doesn't accept it)
        mock_worker_class.assert_called_once_with(
            job_id=4,
            user=None,
            cancel_event=None,
        )
