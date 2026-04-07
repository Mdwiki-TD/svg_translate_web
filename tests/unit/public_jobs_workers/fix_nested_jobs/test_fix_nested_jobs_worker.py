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
            title="Test.svg",
            args={"filename": "Test.svg"},
        )
        assert worker.get_job_type() == "fix_nested_jobs"

    def test_get_initial_result_structure(self) -> None:
        worker = FixNestedJobsWorker(
            task_id=1,
            title="Test.svg",
            args={"filename": "Test.svg"},
        )
        result = worker.get_initial_result()

        assert result["status"] == "pending"
        assert result["started_at"] is not None
        assert result["completed_at"] is None
        assert result["cancelled_at"] is None
        assert result["title"] == "Test.svg"
        assert "stages" in result
        assert "download" in result["stages"]
        assert "analyze" in result["stages"]
        assert "fix" in result["stages"]
        assert "verify" in result["stages"]
        assert "upload" in result["stages"]
        assert "summary" in result
        assert "results" in result

    def test_get_initial_result_stages_have_status(self) -> None:
        worker = FixNestedJobsWorker(
            task_id=1,
            title="Test.svg",
            args={"filename": "Test.svg"},
        )
        result = worker.get_initial_result()

        for _, stage_data in result["stages"].items():
            assert "status" in stage_data
            assert "message" in stage_data
            assert stage_data["status"] == "Pending"

    def test_get_initial_result_summary_structure(self) -> None:
        worker = FixNestedJobsWorker(
            task_id=1,
            title="Test.svg",
            args={"filename": "Test.svg"},
        )
        result = worker.get_initial_result()

        assert "total" in result["summary"]
        assert "success" in result["summary"]
        assert "failed" in result["summary"]
        assert "skipped" in result["summary"]

    def test_worker_init_with_user(self) -> None:
        user = {"username": "testuser", "id": 123}
        worker = FixNestedJobsWorker(
            task_id=1,
            title="Test.svg",
            args={"filename": "Test.svg"},
            user=user,
        )
        assert worker.user == user

    def test_worker_init_with_cancel_event(self) -> None:
        cancel_event = threading.Event()
        worker = FixNestedJobsWorker(
            task_id=1,
            title="Test.svg",
            args={"filename": "Test.svg"},
            cancel_event=cancel_event,
        )
        assert worker.cancel_event is cancel_event


class TestFixNestedJobsWorkerEntry:
    def test_worker_entry_missing_title(self) -> None:
        with patch("src.main_app.public_jobs_workers.fix_nested_jobs.worker.FixNestedJobsWorker"):
            fix_nested_jobs_worker_entry(
                task_id="1",
                title="",
                args={"filename": "Test.svg"},
                user=None,
            )

    def test_worker_entry_missing_args(self) -> None:
        with patch("src.main_app.public_jobs_workers.fix_nested_jobs.worker.FixNestedJobsWorker"):
            fix_nested_jobs_worker_entry(
                task_id="1",
                title="Test.svg",
                args={},
                user=None,
            )

    def test_worker_entry_creates_worker(self) -> None:
        with patch("src.main_app.public_jobs_workers.fix_nested_jobs.worker.FixNestedJobsWorker") as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            fix_nested_jobs_worker_entry(
                task_id="1",
                title="Test.svg",
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
                title="Test.svg",
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
                title="Test.svg",
                args={"filename": "Test.svg"},
                user=None,
                cancel_event=cancel_event,
            )

            call_kwargs = MockWorker.call_args.kwargs
            assert call_kwargs["cancel_event"] is cancel_event
