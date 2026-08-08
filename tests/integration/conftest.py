"""
conftest for integration tests
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.main_app import create_app
from src.main_app.config import TestingConfig
from src.main_app.extensions import db as _db


@pytest.fixture
def admin_jobs_client(monkeypatch: pytest.MonkeyPatch):
    """Return a configured Flask test client paired with a fake jobs mock_jobs_db."""

    monkeypatch.setenv("FLASK_SECRET_KEY", "testing-secret")
    admin_user = SimpleNamespace(username="admin_user", is_active_admin=True)

    def fake_current_user() -> SimpleNamespace:
        return admin_user

    monkeypatch.setattr("src.main_app.public.auth.utils.load_user", fake_current_user)
    monkeypatch.setattr("src.main_app.public.shared_jobs_routes.load_user", fake_current_user)
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
