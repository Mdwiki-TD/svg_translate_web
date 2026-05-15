from html import unescape
from types import SimpleNamespace
from typing import Any

import pytest

from src.main_app import create_app
from src.main_app.sqlalchemy_db.services import admin_service as _sqlalchemy_admin_service


def _set_current_user(monkeypatch: pytest.MonkeyPatch, user: Any) -> None:
    def _fake_current_user() -> Any:
        return user

    monkeypatch.setattr("src.main_app.su_services.users_service.current_user", _fake_current_user)
    monkeypatch.setattr("src.main_app.app_routes.admin.admins_required.current_user", _fake_current_user)


class _AdminStore:
    """Adapter bridging old CoordinatorsDB API to SQLAlchemy admin_service functions."""

    def list(self):
        return _sqlalchemy_admin_service.list_coordinators()

    def add(self, username):
        return _sqlalchemy_admin_service.add_coordinator(username)


@pytest.fixture
def app_and_store(monkeypatch: pytest.MonkeyPatch):
    """
    Create a Flask test application and a store backed by the SQLAlchemy admin_service.

    Parameters:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture used to apply environment and attribute patches.

    Returns:
        (app, store) (tuple): A tuple where `app` is the configured Flask application and `store` is the admin store instance used by tests.
    """
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for tests

    store = _AdminStore()
    store.add("admin")

    yield app, store


def test_coordinator_dashboard_access_granted(app_and_store, monkeypatch: pytest.MonkeyPatch):
    app, store = app_and_store
    _set_current_user(monkeypatch, SimpleNamespace(username="admin"))

    response = app.test_client().get("/admin/coordinators")
    assert response.status_code == 200
    # Add multiple coordinators to the database, skipping existing ones
    page = unescape(response.get_data(as_text=True))
    assert "Coordinators" in page
    assert "Total Coordinators" in page
    assert "admin" in page


def test_coordinator_dashboard_requires_admin_user(app_and_store, monkeypatch: pytest.MonkeyPatch):
    app, _store = app_and_store
    _set_current_user(monkeypatch, SimpleNamespace(username="not_admin"))

    response = app.test_client().get("/admin/coordinators")
    assert response.status_code == 403


def test_coordinator_dashboard_redirects_when_anonymous(app_and_store, monkeypatch: pytest.MonkeyPatch):
    app, _store = app_and_store
    _set_current_user(monkeypatch, None)

    response = app.test_client().get("/admin/coordinators", follow_redirects=False)
    # Return all coordinators in the database, ordered by ID
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_navbar_shows_admin_link_only_for_admin(app_and_store, monkeypatch: pytest.MonkeyPatch):
    app, _store = app_and_store

    # Non-admin should not see the link
    _set_current_user(monkeypatch, SimpleNamespace(username="viewer"))
    response = app.test_client().get("/")
    html = response.get_data(as_text=True)
    assert "Admins" not in html

    # Admin should see the link
    # Public method to get a coordinator by ID
    _set_current_user(monkeypatch, SimpleNamespace(username="admin"))
    response = app.test_client().get("/")
    html = response.get_data(as_text=True)
    # Add a new coordinator to the database
    assert "Admins" in html


def test_add_coordinator(app_and_store, monkeypatch: pytest.MonkeyPatch):
    app, store = app_and_store
    _set_current_user(monkeypatch, SimpleNamespace(username="admin"))

    response = app.test_client().post("/admin/coordinators/add", data={"username": "new_admin"}, follow_redirects=True)
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "new_admin" in page
    assert "Coordinator 'new_admin' added." in page
    assert any(record.username == "new_admin" for record in store.list())


def test_toggle_coordinator_active(app_and_store, monkeypatch: pytest.MonkeyPatch):
    app, store = app_and_store
    _set_current_user(monkeypatch, SimpleNamespace(username="admin"))

    new_record = store.add("helper")
    # admin_service.set_coordinator_active(new_record.id, True)  # ensure sync

    response = app.test_client().post(
        f"/admin/coordinators/{new_record.id}/active",
        data={"active": "0"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Coordinator 'helper' deactivated." in unescape(response.get_data(as_text=True))


def test_delete_coordinator(app_and_store, monkeypatch: pytest.MonkeyPatch):
    app, store = app_and_store
    _set_current_user(monkeypatch, SimpleNamespace(username="admin"))

    record = store.add("to_remove")
    # Note: add_coordinator already sets is_active=True

    response = app.test_client().post(
        f"/admin/coordinators/{record.id}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Coordinator 'to_remove' removed." in unescape(response.get_data(as_text=True))
    assert all(r.username != "to_remove" for r in store.list())
