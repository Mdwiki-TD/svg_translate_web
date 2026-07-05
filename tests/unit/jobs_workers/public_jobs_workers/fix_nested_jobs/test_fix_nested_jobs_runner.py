"""Unit tests for fix_nested_jobs worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

from src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.runner import (
    fix_nested_jobs_worker_entry,
)


class TestFixNestedJobsProcessorEntry:
    def test_worker_entry_missing_args(self) -> None:
        with patch("src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.runner.FixNestedJobsProcessor"):
            fix_nested_jobs_worker_entry(
                job_id=1,
                args={},
                user=None,
            )

    def test_worker_entry_creates_worker(self) -> None:
        with patch(
            "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.runner.FixNestedJobsProcessor"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            fix_nested_jobs_worker_entry(
                job_id=1,
                args={"filename": "Test.svg"},
                user=None,
            )

            MockWorker.assert_called_once()
            mock_instance.run.assert_called_once()

    def test_worker_entry_with_user(self) -> None:
        with patch(
            "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.runner.FixNestedJobsProcessor"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance
            user = {"username": "testuser"}

            fix_nested_jobs_worker_entry(
                job_id=1,
                args={"filename": "Test.svg"},
                user=user,
            )

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["user"] == user

    def test_worker_entry_with_cancel_event(self) -> None:
        with patch(
            "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.runner.FixNestedJobsProcessor"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance
            cancel_event = threading.Event()

            fix_nested_jobs_worker_entry(
                job_id=1,
                args={"filename": "Test.svg"},
                user=None,
                cancel_event=cancel_event,
            )

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["cancel_event"] is cancel_event

    def test_worker_entry_args_is_keyword_only(self) -> None:
        """Test that args is a keyword-only parameter in the new signature."""
        with patch(
            "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.runner.FixNestedJobsProcessor"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            # New signature: (job_id, user, *, cancel_event=None, args=None)
            # args must be keyword-only; user is now the 2nd positional
            fix_nested_jobs_worker_entry(job_id=1, user=None, args={"filename": "Test.svg"})

            MockWorker.assert_called_once_with(
                job_id=1,
                user=None,
                cancel_event=None,
                args={"filename": "Test.svg"},
            )
            mock_instance.run.assert_called_once()

    def test_worker_entry_args_defaults_to_none(self) -> None:
        """Test that args defaults to None when not provided."""
        with patch(
            "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.runner.FixNestedJobsProcessor"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            # Call without args - should default to None
            fix_nested_jobs_worker_entry(job_id=42, user={"username": "tester"})

            MockWorker.assert_called_once_with(
                job_id=42,
                args=None,
                user={"username": "tester"},
                cancel_event=None,
            )

    def test_worker_entry_user_is_second_positional(self) -> None:
        """Test that user is the second positional parameter (after job_id)."""
        user = {"username": "testuser"}
        with patch(
            "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.runner.FixNestedJobsProcessor"
        ) as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            # Pass user as 2nd positional arg (new signature)
            fix_nested_jobs_worker_entry(job_id=77, user=user)

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["user"] is user
