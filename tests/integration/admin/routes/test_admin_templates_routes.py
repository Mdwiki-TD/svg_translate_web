"""Integration tests for the admin template management routes."""

from __future__ import annotations

from html import unescape
from typing import Iterable

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.db.services import delete_service
from src.main_app.db.services import template_service as _sqlalchemy_template_service


class _TemplatesStore:
    """Adapter bridging old TemplatesDB API to SQLAlchemy template_service functions."""

    def list(self, limit=None):
        return _sqlalchemy_template_service.list_templates(limit)

    def add_data(self, data):
        return _sqlalchemy_template_service.add_template_data(data)

    def update_data(self, template_id, data):
        return _sqlalchemy_template_service.update_template_data(template_id, data)

    def delete(self, template_id):
        return delete_service.delete_template(template_id)


@pytest.fixture
def jobs_db(admin_jobs_client):
    store = _TemplatesStore()
    store.add_data({"title": "Existing Template", "main_file": "existing.svg"})
    return store


def snapshot(records: Iterable[TemplateRecord]) -> list[tuple[int, str, str | None]]:
    return [(record.id, record.title, record.main_file) for record in records]


def test_add_template_persists_record_and_flashes_success(admin_jobs_client, jobs_db):
    client = admin_jobs_client

    before = len(jobs_db.list())
    response = client.post(
        "/adminpanel/templates/add",
        data={"title": "New Template", "main_file": "new.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Template 'New Template' added." in page

    records = jobs_db.list()
    assert len(records) == before + 1
    assert any(record.title == "New Template" and record.main_file == "new.svg" for record in records)


def test_update_template_mutates_store_and_flashes_success(admin_jobs_client, jobs_db):
    client = admin_jobs_client
    template_id = jobs_db.list()[0].id

    response = client.post(
        "/adminpanel/templates/update",
        data={"id": str(template_id), "title": "Existing Template", "main_file": "updated.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Template 'Existing Template' main file: updated.svg updated." in page

    record = next(record for record in jobs_db.list() if record.id == template_id)
    assert record.main_file == "updated.svg"


def test_delete_template_removes_record_and_flashes_success(admin_jobs_client, jobs_db):
    client = admin_jobs_client
    template_id = jobs_db.list()[0].id

    response = client.post(
        f"/adminpanel/templates/{template_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Template 'Existing Template' removed." in page
    assert not any(record.id == template_id for record in jobs_db.list())


def test_add_template_requires_title_and_preserves_store(admin_jobs_client, jobs_db):
    client = admin_jobs_client
    before = snapshot(jobs_db.list())

    response = client.post(
        "/adminpanel/templates/add",
        data={"title": " ", "main_file": "ignored.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Title is required to add a template." in page
    assert snapshot(jobs_db.list()) == before


def test_update_template_requires_identifier(admin_jobs_client, jobs_db):
    client = admin_jobs_client
    before = snapshot(jobs_db.list())

    response = client.post(
        "/adminpanel/templates/update",
        data={"id": "", "title": "Existing Template", "main_file": "ignored.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Template ID is required to update a template." in page
    assert snapshot(jobs_db.list()) == before


def test_update_template_requires_title(admin_jobs_client, jobs_db):
    client = admin_jobs_client
    template_id = jobs_db.list()[0].id
    before = snapshot(jobs_db.list())

    response = client.post(
        "/adminpanel/templates/update",
        data={"id": str(template_id), "title": "   ", "main_file": "ignored.svg"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = unescape(response.get_data(as_text=True))
    assert "Title is required to update a template." in page
    assert snapshot(jobs_db.list()) == before
