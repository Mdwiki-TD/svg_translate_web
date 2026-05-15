"""Integration tests for the admin template management routes."""

from __future__ import annotations

from html import unescape
from typing import Iterable

import pytest

from src.main_app import create_app
from src.main_app.db.models import TemplateRecord
from src.main_app.db.services.template_service import TemplatesDB


@pytest.fixture
def jobs_db(mock_sqlite3_db):
    store = TemplatesDB(db=mock_sqlite3_db)
    store.add_data({"title": "Existing Template", "main_file": "existing.svg"})
    return store


@pytest.fixture
def admin_templates_client(monkeypatch: pytest.MonkeyPatch):
    """Return a configured Flask test client with mocked templates service."""
    from types import SimpleNamespace

    admin_user = SimpleNamespace(username="admin_user")

    def fake_current_user():
        return admin_user

    monkeypatch.setattr("src.main_app.su_services.users_service.current_user", fake_current_user)
    monkeypatch.setattr("src.main_app.app_routes.admin.admins_required.current_user", fake_current_user)
    monkeypatch.setattr(
        "src.main_app.app_routes.admin.admins_required.active_coordinators", lambda: {admin_user.username}
    )
    monkeypatch.setattr("src.main_app.db.services.admin_service.active_coordinators", lambda: {admin_user.username})
    monkeypatch.setattr("src.main_app.su_services.users_service.active_coordinators", lambda: {admin_user.username})

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    yield flask_app.test_client()


def snapshot(records: Iterable[TemplateRecord]) -> list[tuple[int, str, str | None]]:
    return [(record.id, record.title, record.main_file) for record in records]


def test_add_template_persists_record_and_flashes_success(admin_templates_client, jobs_db):
    client = admin_templates_client

    before = len(jobs_db.list())
    response = client.post(
        "/admin/templates/add",
        data={"title": "New Template", "main_file": "new.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Template 'New Template' added." in page

    records = jobs_db.list()
    assert len(records) == before + 1
    assert any(record.title == "New Template" and record.main_file == "new.svg" for record in records)


def test_update_template_mutates_store_and_flashes_success(admin_templates_client, jobs_db):
    client = admin_templates_client
    template_id = jobs_db.list()[0].id

    response = client.post(
        "/admin/templates/update",
        data={"id": str(template_id), "title": "Existing Template", "main_file": "updated.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Template 'Existing Template' main file: updated.svg updated." in page

    record = next(record for record in jobs_db.list() if record.id == template_id)
    assert record.main_file == "updated.svg"


def test_delete_template_removes_record_and_flashes_success(admin_templates_client, jobs_db):
    client = admin_templates_client
    template_id = jobs_db.list()[0].id

    response = client.post(
        f"/admin/templates/{template_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Template 'Existing Template' removed." in page
    assert not any(record.id == template_id for record in jobs_db.list())


def test_add_template_requires_title_and_preserves_store(admin_templates_client, jobs_db):
    client = admin_templates_client
    before = snapshot(jobs_db.list())

    response = client.post(
        "/admin/templates/add",
        data={"title": " ", "main_file": "ignored.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Title is required to add a template." in page
    assert snapshot(jobs_db.list()) == before


def test_update_template_requires_identifier(admin_templates_client, jobs_db):
    client = admin_templates_client
    before = snapshot(jobs_db.list())

    response = client.post(
        "/admin/templates/update",
        data={"id": "", "title": "Existing Template", "main_file": "ignored.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Template ID is required to update a template." in page
    assert snapshot(jobs_db.list()) == before


def test_update_template_requires_title(admin_templates_client, jobs_db):
    client = admin_templates_client
    template_id = jobs_db.list()[0].id
    before = snapshot(jobs_db.list())

    response = client.post(
        "/admin/templates/update",
        data={"id": str(template_id), "title": "   ", "main_file": "ignored.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Title is required to update a template." in page
    assert snapshot(jobs_db.list()) == before
