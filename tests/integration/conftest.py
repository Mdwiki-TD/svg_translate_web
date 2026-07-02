"""conftest for the admin jobs management routes."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.main_app.db.services import delete_service
from src.main_app.db.services import jobs_service as _sqlalchemy_jobs_service
from src.main_app import create_app
from src.main_app.config import TestingConfig
from src.main_app.extensions import db as _db

@pytest.fixture
def admin_jobs_client(monkeypatch: pytest.MonkeyPatch):
    """Return a configured Flask test client paired with a fake jobs jobs_db."""

    monkeypatch.setenv("FLASK_SECRET_KEY", "testing-secret")
    admin_user = SimpleNamespace(username="admin_user", is_active_admin=True)

    def fake_current_user() -> SimpleNamespace:
        return admin_user

    monkeypatch.setattr("src.main_app.public.auth.utils.load_user", fake_current_user)
    monkeypatch.setattr("src.main_app.public.jobs_routes_utils.load_user", fake_current_user)
    monkeypatch.setattr("src.main_app.admin.decorators.load_user", fake_current_user)
    monkeypatch.setattr(
        "src.main_app.public.utils.routes_utils._is_admin",
        lambda user: bool(getattr(user, "is_active_admin", False)),
    )

    app = create_app(TestingConfig)
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        real_tables = [t for t in _db.metadata.tables.values() if not t.info.get("is_view")]
        _db.metadata.create_all(_db.engine, tables=real_tables)
        yield app.test_client()
        _db.session.remove()
        _db.metadata.drop_all(_db.engine, tables=real_tables)


class _JobsStore:
    """Adapter bridging old JobsDB API to SQLAlchemy jobs_service functions."""

    def create(self, job_type, username="z"):
        return _sqlalchemy_jobs_service.create_job(job_type, username)

    def list(self, limit=100, job_type=None):
        return _sqlalchemy_jobs_service.list_jobs(limit, job_type)

    def update_status(self, job_id, status, result_file=None, *, job_type):
        return _sqlalchemy_jobs_service.update_job_status(job_id, status, result_file, job_type=job_type)

    def get(self, job_id, job_type):
        return _sqlalchemy_jobs_service.get_job(job_id, job_type)

    def delete(self, job_id, job_type):
        return delete_service.delete_job(job_id, job_type)

    def cancel(self, job_id, job_type=None):
        return _sqlalchemy_jobs_service.cancel_job_db(job_id, job_type)


@pytest.fixture
def jobs_db():
    return _JobsStore()
