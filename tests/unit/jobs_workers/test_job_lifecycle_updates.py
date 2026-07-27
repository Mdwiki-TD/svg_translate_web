from __future__ import annotations

from typing import Any

from flask.app import Flask
from sqlalchemy import text

from src.main_app.db.models.jobs import JobRecord
from src.main_app.db.services.jobs_service import JobsService
from src.main_app.extensions import db
from src.main_app.jobs_workers.base_worker import BaseObjectsJobWorker, WorkerObject


class MockWorker(BaseObjectsJobWorker):
    def __init__(self, job_id: int, job_type_name: str = "mock_job") -> None:
        self.job_id = job_id
        self.args = {}
        self.site = None
        self._job_type_name = job_type_name

        super().__init__(job_id, None, None)

        self.result: WorkerObject = WorkerObject()

    def get_job_type(self) -> str:
        return self._job_type_name

    def process(self) -> dict[str, Any]:
        return self.result.to_json()


def test_before_run_updates_status(mock_app: Flask) -> None:
    with mock_app.app_context():
        job = JobsService().create_job("mock_job_before_run", "test_user")
        worker = MockWorker(job.id, "mock_job_before_run")

        assert worker.result.status == "pending"
        worker.before_run()
        # This is expected to fail currently based on the issue description
        assert worker.result.status == "running"


def test_is_job_cancelled_detects_external_change(mock_app: Flask) -> None:
    with mock_app.app_context():
        job = JobsService().create_job("mock_job_cancel_detect", "test_user")

        # Load the job record into the session's identity map
        _ = db.session.get(JobRecord, job.id)

        assert JobsService().is_job_cancelled(job.id, "mock_job_cancel_detect") is False

        # Update status externally via a raw connection (bypassing ORM)
        with db.engine.connect() as conn:
            conn.execute(text("UPDATE jobs SET status = 'cancelled' WHERE id = :id"), {"id": job.id})
            conn.commit()

        # Expire all ORM objects so they re-read from DB on next access
        db.session.expire_all()

        # Now JobsService().is_job_cancelled should return True.
        assert JobsService().is_job_cancelled(job.id, "mock_job_cancel_detect") is True


def test_is_cancelled_sets_cancelled_at(mock_app: Flask) -> None:
    with mock_app.app_context():
        job = JobsService().create_job("mock_job_cancelled_at", "test_user")
        worker = MockWorker(job.id, "mock_job_cancelled_at")

        # Manually cancel in DB via raw connection (bypassing ORM)
        with db.engine.connect() as conn:
            conn.execute(text("UPDATE jobs SET status = 'cancelled' WHERE id = :id"), {"id": job.id})
            conn.commit()

        # Expire all ORM objects so they re-read from DB on next access
        db.session.expire_all()

        assert worker.result.cancelled_at is None
        assert worker.is_cancelled() is False
        assert worker.is_cancelled(check_db=True) is True
        assert worker.result.status == "cancelled"
        assert worker.result.cancelled_at is not None
