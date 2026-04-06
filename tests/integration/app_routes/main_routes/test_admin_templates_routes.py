"""Integration tests for the admin template management routes."""

from __future__ import annotations

from html import unescape
from typing import Iterable
from unittest.mock import MagicMock

import pytest

from src.main_app import create_app
from src.main_app.services.template_service import TemplateRecord


class FakeTemplatesDB:
    """Fake in-memory templates store for testing."""

    def __init__(self):
        self._templates = {}
        self._next_id = 1

    def add_data(self, data: dict) -> TemplateRecord:
        title = data.get("title", "")
        rec = TemplateRecord(
            id=self._next_id,
            title=title,
            main_file=data.get("main_file", ""),
            last_world_file=data.get("last_world_file", ""),
            last_world_year=data.get("last_world_year"),
            source=data.get("source", ""),
        )
        self._templates[self._next_id] = rec
        self._next_id += 1
        return rec

    def list(self) -> list[TemplateRecord]:
        return list(self._templates.values())

    def fetch_by_id(self, template_id: int) -> TemplateRecord:
        if template_id not in self._templates:
            raise LookupError(f"Template id {template_id} was not found")
        return self._templates[template_id]

    def delete(self, template_id: int) -> TemplateRecord:
        rec = self.fetch_by_id(template_id)
        del self._templates[template_id]
        return rec

    def update_template_data(self, template_id: int, data: dict) -> TemplateRecord:
        rec = self.fetch_by_id(template_id)
        if "title" in data and data["title"] is not None:
            rec.title = data["title"]
        if "main_file" in data and data["main_file"] is not None:
            rec.main_file = data["main_file"]
        if "last_world_file" in data and data["last_world_file"] is not None:
            rec.last_world_file = data["last_world_file"]
        if "last_world_year" in data and data["last_world_year"] is not None:
            rec.last_world_year = data["last_world_year"]
        if "source" in data and data["source"] is not None:
            rec.source = data["source"]
        self._templates[template_id] = rec
        return rec


@pytest.fixture
def admin_templates_client(monkeypatch: pytest.MonkeyPatch):
    """Return a configured Flask test client with mocked templates service."""
    from types import SimpleNamespace

    admin_user = SimpleNamespace(username="admin_user")

    def fake_current_user():
        return admin_user

    monkeypatch.setenv("FLASK_SECRET_KEY", "testing-secret")
    monkeypatch.setattr("src.main_app.services.users_service.current_user", fake_current_user)
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.templates.current_user", fake_current_user)
    monkeypatch.setattr("src.main_app.app_routes.admin.admins_required.current_user", fake_current_user)
    monkeypatch.setattr(
        "src.main_app.app_routes.admin.admins_required.active_coordinators", lambda: {admin_user.username}
    )
    monkeypatch.setattr("src.main_app.services.admin_service.active_coordinators", lambda: {admin_user.username})
    monkeypatch.setattr("src.main_app.services.users_service.active_coordinators", lambda: {admin_user.username})

    store = FakeTemplatesDB()
    store.add_data({"title": "Existing Template", "main_file": "existing.svg"})

    mock_service = MagicMock()
    mock_service.list_templates.return_value = store.list()
    mock_service.add_template_data.side_effect = store.add_data
    mock_service.update_template_data.side_effect = store.update_template_data
    mock_service.delete_template.side_effect = store.delete

    def fake_get_template(template_id: int):
        return store.fetch_by_id(template_id)

    mock_service.get_template.side_effect = fake_get_template
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.templates.template_service", mock_service)

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    yield flask_app.test_client(), store


def snapshot(records: Iterable[TemplateRecord]) -> list[tuple[int, str, str | None]]:
    return [(record.id, record.title, record.main_file) for record in records]


def test_add_template_persists_record_and_flashes_success(admin_templates_client):
    client, store = admin_templates_client

    before = len(store.list())
    response = client.post(
        "/admin/templates/add",
        data={"title": "New Template", "main_file": "new.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Template 'New Template' added." in page

    records = store.list()
    assert len(records) == before + 1
    assert any(record.title == "New Template" and record.main_file == "new.svg" for record in records)


def test_update_template_mutates_store_and_flashes_success(admin_templates_client):
    client, store = admin_templates_client
    template_id = store.list()[0].id

    response = client.post(
        "/admin/templates/update",
        data={"id": str(template_id), "title": "Existing Template", "main_file": "updated.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Template 'Existing Template' main file: updated.svg updated." in page

    record = next(record for record in store.list() if record.id == template_id)
    assert record.main_file == "updated.svg"


def test_delete_template_removes_record_and_flashes_success(admin_templates_client):
    client, store = admin_templates_client
    template_id = store.list()[0].id

    response = client.post(
        f"/admin/templates/{template_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Template 'Existing Template' removed." in page
    assert not any(record.id == template_id for record in store.list())


def test_add_template_requires_title_and_preserves_store(admin_templates_client):
    client, store = admin_templates_client
    before = snapshot(store.list())

    response = client.post(
        "/admin/templates/add",
        data={"title": " ", "main_file": "ignored.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Title is required to add a template." in page
    assert snapshot(store.list()) == before


def test_update_template_requires_identifier(admin_templates_client):
    client, store = admin_templates_client
    before = snapshot(store.list())

    response = client.post(
        "/admin/templates/update",
        data={"id": "", "title": "Existing Template", "main_file": "ignored.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Template ID is required to update a template." in page
    assert snapshot(store.list()) == before


def test_update_template_requires_title(admin_templates_client):
    client, store = admin_templates_client
    template_id = store.list()[0].id
    before = snapshot(store.list())

    response = client.post(
        "/admin/templates/update",
        data={"id": str(template_id), "title": "   ", "main_file": "ignored.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Title is required to update a template." in page
    assert snapshot(store.list()) == before
