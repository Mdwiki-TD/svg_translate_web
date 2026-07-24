"""Tests for delete_service.py."""

from __future__ import annotations

from src.main_app.db.models import (
    JobRecord,
    UserRecord,
)
from src.main_app.db.services.delete_service import (
    delete_job,
    delete_record_by_pk,
)
from src.main_app.extensions import db as _db


class TestDeleteRecordByPk:
    def test_delete_existing_record(self, mock_app, setup_db):
        with mock_app.app_context():
            record = UserRecord(username="testuser", user_id=100)
            _db.session.add(record)
            _db.session.commit()

            result = delete_record_by_pk(UserRecord, record.user_id)
            assert result is True
            _db.session.expire_all()
            assert _db.session.get(UserRecord, record.user_id) is None

    def test_delete_non_existent_record(self, mock_app, setup_db):
        with mock_app.app_context():
            result = delete_record_by_pk(UserRecord, 99999)
            assert result is False

    def test_delete_with_none_pk(self, mock_app, setup_db):
        with mock_app.app_context():
            result = delete_record_by_pk(UserRecord, None)
            assert result is False


class TestDeleteJob:
    def test_delete_existing_job(self, mock_app, setup_db):
        with mock_app.app_context():
            record = JobRecord(job_type="copy_svg_langs", status="completed", username="admin")
            _db.session.add(record)
            _db.session.commit()
            job_id = record.id

            result = delete_job(job_id, "copy_svg_langs")
            assert result is True
            _db.session.expire_all()
            assert _db.session.get(JobRecord, job_id) is None

    def test_delete_non_existent_job(self, mock_app, setup_db):
        with mock_app.app_context():
            result = delete_job(99999, "copy_svg_langs")
            assert result is False

    def test_delete_job_wrong_type(self, mock_app, setup_db):
        """Deleting with wrong job_type should not delete."""
        with mock_app.app_context():
            record = JobRecord(job_type="copy_svg_langs", status="completed", username="admin")
            _db.session.add(record)
            _db.session.commit()
            job_id = record.id

            result = delete_job(job_id, "wrong_type")
            assert result is False
            _db.session.expire_all()
            assert _db.session.get(JobRecord, job_id) is not None
