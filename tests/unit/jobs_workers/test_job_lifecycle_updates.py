from __future__ import annotations

from typing import Any

from flask.app import Flask

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
        # JobsService().is_job_cancelled currently uses scalar query which MIGHT avoid identity map,
        # but let's see if we can make it fail by loading the record.
        _ = db.session.get(JobRecord, job.id)

        assert JobsService().is_job_cancelled(job.id, "mock_job_cancel_detect") is False

        # Update status externally via a different session
        # In this test environment, we can just use a separate engine or connection
        with db.engine.connect() as conn:
            conn.execute(db.text("UPDATE jobs SET status = 'cancelled' WHERE id = :id"), {"id": job.id})
            conn.commit()

        # Now JobsService().is_job_cancelled should return True.
        # If it uses a session that has a stale view of the world, it might return False
        # (especially if the isolation level was REPEATABLE READ, but even in READ COMMITTED,
        # SQLAlchemy might cache some things if not careful).
        # Actually, scalar query usually DOES go to the DB, but let's see.
        # IF it passes, it means scalar() bypasses the identity map or it's not in it.
        # But let's try to get the record again via ORM.
        job_after = db.session.get(JobRecord, job.id)
        assert job_after.status == "pending"  # It is stale here!

        assert JobsService().is_job_cancelled(job.id, "mock_job_cancel_detect") is True

        # After JobsService().is_job_cancelled calls refresh, job_after should also be updated if it's the same object
        assert job_after.status == "cancelled"


def test_is_cancelled_sets_cancelled_at(mock_app: Flask) -> None:
    with mock_app.app_context():
        job = JobsService().create_job("mock_job_cancelled_at", "test_user")
        worker = MockWorker(job.id, "mock_job_cancelled_at")

        # Manually cancel in DB
        with db.engine.connect() as conn:
            conn.execute(db.text("UPDATE jobs SET status = 'cancelled' WHERE id = :id"), {"id": job.id})
            conn.commit()

        assert worker.result.cancelled_at is None
        assert worker.is_cancelled() is False
        assert worker.is_cancelled(check_db=True) is True
        assert worker.result.status == "cancelled"
        assert worker.result.cancelled_at is not None
