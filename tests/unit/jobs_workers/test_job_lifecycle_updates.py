from __future__ import annotations


import pytest
from flask.app import Flask
from sqlalchemy import text

from src.main_app.database.models.jobs import JobRecord
from src.main_app.database.services.jobs_service import JobsService
from src.main_app.extensions import db
from src.main_app.jobs_workers.base_worker import BaseObjectsJobWorker, WorkerMapping
from src.main_app.jobs_workers.objects import JobsRunner


class MockWorker(BaseObjectsJobWorker):
    def __init__(self, job_id: int, job_type_name: str = "mock_job") -> None:
        self.args = {}
        self.site = None
        self._job_type_name = job_type_name

        super().__init__(JobsRunner(job_id=job_id, user={}))

        self.result: WorkerMapping = WorkerMapping()

    def get_job_type(self) -> str:
        return self._job_type_name

    def process(self) -> WorkerMapping:
        return self.result


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.job_service = JobsService()


class TestJob(TestSetup):
    def test_before_run_updates_status(self, mock_app: Flask) -> None:
        with mock_app.app_context():
            job = self.job_service.create_job("mock_job_before_run", "test_user")
            worker = MockWorker(job.id, "mock_job_before_run")

            assert worker.result.status == "pending"
            worker.before_run()
            # This is expected to fail currently based on the issue description
            assert worker.result.status == "running"

    def test_is_job_cancelled_detects_external_change(self, mock_app: Flask) -> None:
        with mock_app.app_context():
            job = self.job_service.create_job("mock_job_cancel_detect", "test_user")

            # Load the job record into the session's identity map
            _ = db.session.get(JobRecord, job.id)

            assert self.job_service.is_job_cancelled(job.id, "mock_job_cancel_detect") is False

            # Update status externally via a raw connection (bypassing ORM)
            with db.engine.connect() as conn:
                conn.execute(text("UPDATE jobs SET status = 'cancelled' WHERE id = :id"), {"id": job.id})
                conn.commit()

            # Expire all ORM objects so they re-read from DB on next access
            db.session.expire_all()

            # Now self.job_service.is_job_cancelled should return True.
            assert self.job_service.is_job_cancelled(job.id, "mock_job_cancel_detect") is True

    def test_is_cancelled_sets_cancelled_at(self, mock_app: Flask) -> None:
        with mock_app.app_context():
            job = self.job_service.create_job("mock_job_cancelled_at", "test_user")
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
