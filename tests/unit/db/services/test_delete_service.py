"""Tests for delete_service.py."""

from __future__ import annotations

import pytest

from src.main_app.db.models import (
    AdminUserRecord,
    JobRecord,
    OwidChartRecord,
    OwidSlugRedirectRecord,
    SettingRecord,
    TemplateRecord,
    UseRecord,
    UserTokenRecord,
)
from src.main_app.db.services.delete_service import (
    delete_chart,
    delete_coordinator,
    delete_job,
    delete_record_by_pk,
    delete_setting_by_key,
    delete_slug_redirect,
    delete_template,
    delete_user,
    delete_user_token,
)
from src.main_app.extensions import db as _db


class TestDeleteRecordByPk:
    def test_delete_existing_record(self, mock_app, setup_db):
        with mock_app.app_context():
            record = UseRecord(username="testuser", user_id=100)
            _db.session.add(record)
            _db.session.commit()

            result = delete_record_by_pk(UseRecord, record.user_id)
            assert result is True
            _db.session.expire_all()
            assert _db.session.get(UseRecord, record.user_id) is None

    def test_delete_non_existent_record(self, mock_app, setup_db):
        with mock_app.app_context():
            result = delete_record_by_pk(UseRecord, 99999)
            assert result is False

    def test_delete_with_none_pk(self, mock_app, setup_db):
        with mock_app.app_context():
            result = delete_record_by_pk(UseRecord, None)
            assert result is False


class TestDeleteUserToken:
    def test_delete_existing_token(self, mock_app, setup_db):
        with mock_app.app_context():
            # UserTokenRecord FK → UseRecord
            user = UseRecord(username="token_user", user_id=200)
            _db.session.add(user)
            _db.session.commit()

            record = UserTokenRecord(user_id=200, access_token=b"enc", access_secret=b"enc2")
            _db.session.add(record)
            _db.session.commit()

            result = delete_user_token(200)
            assert result is True
            _db.session.expire_all()
            assert _db.session.get(UserTokenRecord, 200) is None

    def test_delete_non_existent_token(self, mock_app, setup_db):
        with mock_app.app_context():
            result = delete_user_token(99999)
            assert result is False


class TestDeleteUser:
    def test_delete_existing_user(self, mock_app, setup_db):
        with mock_app.app_context():
            record = UseRecord(username="delete_me", user_id=300)
            _db.session.add(record)
            _db.session.commit()

            result = delete_user(300)
            assert result is True
            _db.session.expire_all()
            assert _db.session.get(UseRecord, 300) is None

    def test_delete_non_existent_user(self, mock_app, setup_db):
        with mock_app.app_context():
            result = delete_user(99999)
            assert result is False


class TestDeleteCoordinator:
    def test_delete_existing_coordinator(self, mock_app, setup_db):
        with mock_app.app_context():
            # AdminUserRecord FK → UseRecord, so create a user first
            user = UseRecord(username="admin_user", user_id=401)
            _db.session.add(user)
            _db.session.commit()

            record = AdminUserRecord(username="admin_user", is_active=True)
            _db.session.add(record)
            _db.session.commit()

            result = delete_coordinator(record.id)
            assert result is True
            _db.session.expire_all()
            assert _db.session.get(AdminUserRecord, record.id) is None

    def test_delete_non_existent_coordinator(self, mock_app, setup_db):
        with mock_app.app_context():
            result = delete_coordinator(99999)
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


class TestDeleteChart:
    def test_delete_existing_chart(self, mock_app, setup_db):
        with mock_app.app_context():
            # OwidChartRecord has PK chart_id, not id
            record = OwidChartRecord(slug="test-slug", title="Test Chart")
            _db.session.add(record)
            _db.session.commit()

            result = delete_chart(record.chart_id)
            assert result is True
            _db.session.expire_all()
            assert _db.session.get(OwidChartRecord, record.chart_id) is None

    def test_delete_non_existent_chart(self, mock_app, setup_db):
        with mock_app.app_context():
            result = delete_chart(99999)
            assert result is False


class TestDeleteSetting:
    def test_delete_existing_setting(self, mock_app, setup_db):
        with mock_app.app_context():
            record = SettingRecord(key="test_setting", title="Test", value="val", value_type="string")
            _db.session.add(record)
            _db.session.commit()

            result = delete_setting_by_key("test_setting")
            assert result is True
            _db.session.expire_all()
            assert _db.session.get(SettingRecord, record.id) is None

    def test_delete_non_existent_setting(self, mock_app, setup_db):
        with mock_app.app_context():
            result = delete_setting_by_key("nonexistent_key")
            assert result is False


class TestDeleteSlugRedirect:
    def test_delete_existing_redirect(self, mock_app, setup_db):
        with mock_app.app_context():
            # OwidSlugRedirectRecord requires redirect_to (NOT NULL)
            record = OwidSlugRedirectRecord(slug="old-slug", redirect_to="new-slug")
            _db.session.add(record)
            _db.session.commit()

            result = delete_slug_redirect(record.id)
            assert result is True
            _db.session.expire_all()
            assert _db.session.get(OwidSlugRedirectRecord, record.id) is None

    def test_delete_non_existent_redirect(self, mock_app, setup_db):
        with mock_app.app_context():
            result = delete_slug_redirect(99999)
            assert result is False


class TestDeleteTemplate:
    def test_delete_existing_template(self, mock_app, setup_db):
        with mock_app.app_context():
            record = TemplateRecord(title="Template:Test", page_id=500)
            _db.session.add(record)
            _db.session.commit()

            result = delete_template(record.id)
            assert result is True
            _db.session.expire_all()
            assert _db.session.get(TemplateRecord, record.id) is None

    def test_delete_non_existent_template(self, mock_app, setup_db):
        with mock_app.app_context():
            result = delete_template(99999)
            assert result is False
