from __future__ import annotations

from src.main_app.database.models.jobs import JobRecord


def test_job_record_creation(sqlite_db) -> None:
    job = JobRecord(job_type="test_job", username="test_user")
    sqlite_db.session.add(job)
    sqlite_db.session.commit()
    sqlite_db.session.refresh(job)

    assert job.id is not None
    assert job.job_type == "test_job"
    assert job.username == "test_user"
    assert job.status == "pending"
    assert job.created_at is not None
    assert job.updated_at is not None
