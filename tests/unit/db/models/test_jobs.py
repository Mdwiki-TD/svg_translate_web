from __future__ import annotations

from flask.app import Flask

from src.main_app.db.models.jobs import JobRecord
from src.main_app.extensions import db


def test_job_record_creation(mock_app: Flask) -> None:
    with mock_app.app_context():
        job = JobRecord(job_type="test_job", username="test_user")
        db.session.add(job)
        db.session.commit()
        db.session.refresh(job)

        assert job.id is not None
        assert job.job_type == "test_job"
        assert job.username == "test_user"
        assert job.status == "pending"
        assert job.created_at is not None
        assert job.updated_at is not None
