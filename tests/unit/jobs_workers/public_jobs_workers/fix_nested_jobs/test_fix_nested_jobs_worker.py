"""Unit tests for fix_nested_jobs worker module."""

from __future__ import annotations

import threading

from src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker import (
    FixNestedJobsProcessor,
)


class TestFixNestedJobsProcessor:
    def test_get_job_type(self) -> None:
        worker = FixNestedJobsProcessor(
            job_id=1,
            user=None,
            args={"filename": "Test.svg"},
        )
        assert worker.get_job_type() == "fix_nested_jobs"

    def test_result_initial_structure(self) -> None:
        worker = FixNestedJobsProcessor(
            job_id=1,
            user=None,
            args={"filename": "Test.svg"},
        )
        result = worker.result

        assert result.status == "pending"
        assert result.started_at is not None
        assert result.completed_at is None
        assert result.cancelled_at is None
        assert result.filename is None  # filename comes from args, not set until processor runs
        assert result.stages.download.status == "pending"
        assert result.stages.analyze.status == "pending"
        assert result.stages.fix.status == "pending"
        assert result.stages.verify.status == "pending"
        assert result.stages.upload.status == "pending"

    def test_worker_init_with_user(self) -> None:
        user = {"username": "testuser", "id": 123}
        worker = FixNestedJobsProcessor(
            job_id=1,
            args={"filename": "Test.svg"},
            user=user,
        )
        assert worker.user == user

    def test_worker_init_with_cancel_event(self) -> None:
        cancel_event = threading.Event()
        worker = FixNestedJobsProcessor(
            job_id=1,
            user=None,
            args={"filename": "Test.svg"},
            cancel_event=cancel_event,
        )
        assert worker.cancel_event is cancel_event
