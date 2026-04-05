"""Integration tests for the admin template management routes."""

from __future__ import annotations

from html import unescape
from typing import Iterable
from src.main_app.services.template_service import TemplateRecord


def snapshot(records: Iterable[TemplateRecord]) -> list[tuple[int, str, str | None]]:
    return [(record.id, record.title, record.main_file) for record in records]


def test_templates_dashboard_lists_existing_records(admin_templates_client):
    client, store = admin_templates_client

    store.add("Second Template", "second.svg")

    response = client.get("/admin/templates")
    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Templates" in page
    assert "Existing Template" in page
    assert "Second Template" in page
    assert "second.svg" in page


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
