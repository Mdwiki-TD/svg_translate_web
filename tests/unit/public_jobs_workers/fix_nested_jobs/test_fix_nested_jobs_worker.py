"""Unit tests for fix_nested_jobs worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

from src.main_app.public_jobs_workers.fix_nested_jobs.worker import (
    FixNestedJobsWorker,
    fix_nested_jobs_worker_entry,
)


class TestFixNestedJobsWorker:
    def test_get_job_type(self) -> None:
        worker = FixNestedJobsWorker(
            task_id=1,
            args={"filename": "Test.svg"},
        )
        assert worker.get_job_type() == "fix_nested_jobs"

    def test_get_initial_result_structure(self) -> None:
        worker = FixNestedJobsWorker(
            task_id=1,
            args={"filename": "Test.svg"},
        )
        result = worker.get_initial_result()

        assert result["status"] == "pending"
        assert result["started_at"] is not None
        assert result["completed_at"] is None
        assert result["cancelled_at"] is None
        assert result["filename"] is None  # filename comes from args, not set until processor runs
        assert "stages" in result
        assert "download" in result["stages"]
        assert "analyze" in result["stages"]
        assert "fix" in result["stages"]
        assert "verify" in result["stages"]
        assert "upload" in result["stages"]

    def test_get_initial_result_stages_have_status(self) -> None:
        worker = FixNestedJobsWorker(
            task_id=1,
            args={"filename": "Test.svg"},
        )
        result = worker.get_initial_result()

        for _, stage_data in result["stages"].items():
            assert "status" in stage_data
            assert "message" in stage_data
            assert stage_data["status"] == "Pending"

    def test_worker_init_with_user(self) -> None:
        user = {"username": "testuser", "id": 123}
        worker = FixNestedJobsWorker(
            task_id=1,
            args={"filename": "Test.svg"},
            user=user,
        )
        assert worker.user == user

    def test_worker_init_with_cancel_event(self) -> None:
        cancel_event = threading.Event()
        worker = FixNestedJobsWorker(
            task_id=1,
            args={"filename": "Test.svg"},
            cancel_event=cancel_event,
        )
        assert worker.cancel_event is cancel_event


class TestFixNestedJobsWorkerEntry:
    def test_worker_entry_missing_args(self) -> None:
        with patch("src.main_app.public_jobs_workers.fix_nested_jobs.worker.FixNestedJobsWorker"):
            fix_nested_jobs_worker_entry(
                task_id="1",
                args={},
                user=None,
            )

    def test_worker_entry_creates_worker(self) -> None:
        with patch("src.main_app.public_jobs_workers.fix_nested_jobs.worker.FixNestedJobsWorker") as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            fix_nested_jobs_worker_entry(
                task_id="1",
                args={"filename": "Test.svg"},
                user=None,
            )

            MockWorker.assert_called_once()
            mock_instance.run.assert_called_once()

    def test_worker_entry_with_user(self) -> None:
        with patch("src.main_app.public_jobs_workers.fix_nested_jobs.worker.FixNestedJobsWorker") as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance
            user = {"username": "testuser"}

            fix_nested_jobs_worker_entry(
                task_id="1",
                args={"filename": "Test.svg"},
                user=user,
            )

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["user"] == user

    def test_worker_entry_with_cancel_event(self) -> None:
        with patch("src.main_app.public_jobs_workers.fix_nested_jobs.worker.FixNestedJobsWorker") as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance
            cancel_event = threading.Event()

            fix_nested_jobs_worker_entry(
                task_id="1",
                args={"filename": "Test.svg"},
                user=None,
                cancel_event=cancel_event,
            )

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["cancel_event"] is cancel_event

    def test_worker_entry_args_is_keyword_only(self) -> None:
        """Test that args is a keyword-only parameter in the new signature."""
        with patch("src.main_app.public_jobs_workers.fix_nested_jobs.worker.FixNestedJobsWorker") as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            # New signature: (task_id, user, *, cancel_event=None, args=None)
            # args must be keyword-only; user is now the 2nd positional
            fix_nested_jobs_worker_entry("1", None, args={"filename": "Test.svg"})

            MockWorker.assert_called_once_with(
                task_id="1",
                args={"filename": "Test.svg"},
                user=None,
                cancel_event=None,
            )
            mock_instance.run.assert_called_once()

    def test_worker_entry_args_defaults_to_none(self) -> None:
        """Test that args defaults to None when not provided."""
        with patch("src.main_app.public_jobs_workers.fix_nested_jobs.worker.FixNestedJobsWorker") as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            # Call without args - should default to None
            fix_nested_jobs_worker_entry("42", {"username": "tester"})

            MockWorker.assert_called_once_with(
                task_id="42",
                args=None,
                user={"username": "tester"},
                cancel_event=None,
            )

    def test_worker_entry_user_is_second_positional(self) -> None:
        """Test that user is the second positional parameter (after task_id)."""
        user = {"username": "testuser"}
        with patch("src.main_app.public_jobs_workers.fix_nested_jobs.worker.FixNestedJobsWorker") as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            # Pass user as 2nd positional arg (new signature)
            fix_nested_jobs_worker_entry("77", user)

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["user"] is user
