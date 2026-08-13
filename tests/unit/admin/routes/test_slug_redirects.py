"""Tests for src/main_app/adminpanel/routes/slug_redirects.py."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Blueprint
from werkzeug.datastructures import MultiDict

from src.main_app.admin.routes.slug_redirects import (  # SlugFuncs,
    SlugRedirectsRoutes,
)
from src.main_app.database.services import OwidSlugRedirectsService
from src.main_app.extensions import db as _db


@pytest.fixture(autouse=True)
def _fake_admin_user(monkeypatch):
    """Fake an authenticated admin user for all tests in this module."""
    admin_user = SimpleNamespace(username="test_admin", is_active_admin=True)
    monkeypatch.setattr("src.main_app.admin.decorators.load_user", lambda: admin_user)
    monkeypatch.setattr("src.main_app.public.auth.utils.load_user", lambda: admin_user)
    monkeypatch.setattr("src.main_app.public.utils.routes_utils.load_user", lambda: admin_user)


@pytest.fixture
def client(mock_app):
    """Test client bound to mock_app."""
    return mock_app.test_client()


class TestEditSlugRedirect:
    """Direct tests for the edit_slug_redirect method via HTTP."""

    def test_with_found_record(self, client):
        """edit should render the record's data when found."""
        service = OwidSlugRedirectsService()
        record = service.add_new_slug_redirect(slug="test-slug", redirect_to="/target")
        assert record is not None, "failed to seed slug redirect"
        resp = client.get(f"/adminpanel/slugredirects/{record.id}/edit")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "test-slug" in html
        assert "/target" in html

    def test_with_not_found_record(self, client):
        """edit should show error when record is missing."""
        resp = client.get("/adminpanel/slugredirects/99999/edit")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Redirect record not found" in html


class TestSlugRedirectsClass:
    """Tests for the SlugRedirectsRoutes class itself."""

    def test_blueprint_properties(self):
        """SlugRedirectsRoutes should create a Blueprint with the expected name and prefix."""
        instance = SlugRedirectsRoutes(Blueprint("slugredirects", __name__, url_prefix="/slugredirects"))
        assert instance.bp.name == "slugredirects"
        assert instance.bp.url_prefix == "/slugredirects"

    def test_all_routes_registered(self):
        """SlugRedirectsRoutes should register all 5 routes."""
        instance = SlugRedirectsRoutes(Blueprint("slugredirects", __name__, url_prefix="/slugredirects"))
        assert len(instance.bp.deferred_functions) == 5


class TestSlugRedirectsRoutes:
    """Route-level tests using mock_app's test client with real DB/services."""

    def _seed_redirect(self, slug: str = "test-slug", redirect_to: str = "/target"):
        """Seed a slug redirect record via the real service."""
        service = OwidSlugRedirectsService()
        record = service.add_new_slug_redirect(slug=slug, redirect_to=redirect_to)
        assert record is not None, f"failed to seed slug redirect {slug}"
        return record

    def _seed_redirects(self, count: int = 2):
        """Seed multiple slug redirect records."""
        service = OwidSlugRedirectsService()
        for i in range(count):
            service.add_new_slug_redirect(slug=f"slug-{i}", redirect_to=f"/target-{i}")
        return service.list_slug_redirects()

    # ── dashboard (GET /) ────────────────────────────────────────────────

    def test_dashboard_lists_records(self, client):
        """Dashboard should list all slug redirect records."""
        self._seed_redirects(2)

        resp = client.get("/adminpanel/slugredirects/")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "slug-0" in html
        assert "slug-1" in html

    # ── edit (GET /<id>/edit) ────────────────────────────────────────────

    def test_edit_get_found(self, client):
        """GET /<id>/edit should render the edit form with the record."""
        record = self._seed_redirect(slug="edit-test")

        resp = client.get(f"/adminpanel/slugredirects/{record.id}/edit")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "edit-test" in html

    def test_edit_get_not_found(self, client):
        """GET /<id>/edit for a missing record should render with an error."""
        resp = client.get("/adminpanel/slugredirects/99999/edit")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Redirect record not found" in html

    # ── update (POST /update) ────────────────────────────────────────────

    def test_update_success(self, client):
        """POST /update with valid data should update and redirect."""
        record = self._seed_redirect(slug="update-test")

        resp = client.post(
            "/adminpanel/slugredirects/update",
            data={"id": record.id, "should_be_replaced": "on"},
        )

        assert resp.status_code == 302
        _db.session.expire_all()
        updated = OwidSlugRedirectsService().get_slug_redirect_by_id(record.id)
        assert updated.should_be_replaced is True

    def test_update_missing_id(self, client):
        """POST /update without an id should not call the service and redirect."""
        resp = client.post(
            "/adminpanel/slugredirects/update",
            data={"should_be_replaced": "on"},
        )

        assert resp.status_code == 302

    def test_update_not_found(self, client):
        """POST /update when record does not exist should redirect."""
        resp = client.post(
            "/adminpanel/slugredirects/update",
            data={"id": 99999, "should_be_replaced": "on"},
        )

        assert resp.status_code == 302

    def test_update_with_from_popup(self, client):
        """POST /update with from_popup=1 should render popup_action.html."""
        record = self._seed_redirect(slug="popup-test")

        resp = client.post(
            "/adminpanel/slugredirects/update",
            data={"id": record.id, "should_be_replaced": "on", "from_popup": "1"},
        )

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "Action Completed" in html

    # ── delete (POST /<id>/delete) ───────────────────────────────────────

    def test_delete_success(self, client):
        """POST /<id>/delete should delete and redirect on success."""
        record = self._seed_redirect(slug="delete-test")

        resp = client.post(f"/adminpanel/slugredirects/{record.id}/delete")

        assert resp.status_code == 302
        assert OwidSlugRedirectsService().get_slug_redirect_by_id(record.id) is None

    def test_delete_not_found(self, client):
        """POST /<id>/delete should redirect when the record is not found."""
        resp = client.post("/adminpanel/slugredirects/99999/delete")

        assert resp.status_code == 302

    # ── bulk_action (POST /bulk_action) ──────────────────────────────────

    def test_bulk_mark_replace(self, client):
        """POST /bulk_action with action=mark_replace should bulk update."""
        records = self._seed_redirects(3)
        ids = [r.id for r in records]

        form_data = MultiDict([("action", "mark_replace")])
        for rid in ids:
            form_data.add("selected_ids", str(rid))

        resp = client.post(
            "/adminpanel/slugredirects/bulk_action",
            data=form_data,
        )

        assert resp.status_code == 302
        _db.session.expire_all()
        for r in OwidSlugRedirectsService().list_slug_redirects():
            assert r.should_be_replaced is True

    def test_bulk_mark_no_replace(self, client):
        """POST /bulk_action with action=mark_no_replace should set should_be_replaced=False."""
        record = self._seed_redirect(slug="noreplace-test")

        resp = client.post(
            "/adminpanel/slugredirects/bulk_action",
            data={"action": "mark_no_replace", "selected_ids": [str(record.id)]},
        )

        assert resp.status_code == 302
        _db.session.expire_all()
        updated = OwidSlugRedirectsService().get_slug_redirect_by_id(record.id)
        assert updated.should_be_replaced is False

    def test_bulk_delete_action(self, client):
        """POST /bulk_action with action=delete should bulk delete."""
        records = self._seed_redirects(2)
        ids = [r.id for r in records]

        form_data = MultiDict([("action", "delete")])
        for rid in ids:
            form_data.add("selected_ids", str(rid))

        resp = client.post(
            "/adminpanel/slugredirects/bulk_action",
            data=form_data,
        )

        assert resp.status_code == 302
        assert len(OwidSlugRedirectsService().list_slug_redirects()) == 0

    def test_bulk_invalid_action(self, client):
        """POST /bulk_action with an invalid action should not delete or update records."""
        record = self._seed_redirect(slug="invalid-test")

        resp = client.post(
            "/adminpanel/slugredirects/bulk_action",
            data={"action": "invalid", "selected_ids": [str(record.id)]},
        )

        assert resp.status_code == 302
        assert len(OwidSlugRedirectsService().list_slug_redirects()) == 1

    def test_bulk_no_items_selected(self, client):
        """POST /bulk_action without selected_ids should not call any service."""
        self._seed_redirects(2)

        resp = client.post(
            "/adminpanel/slugredirects/bulk_action",
            data={"action": "mark_replace"},
        )

        assert resp.status_code == 302
        assert len(OwidSlugRedirectsService().list_slug_redirects()) == 2

    def test_bulk_action_exception(self, client):
        """POST /bulk_action with valid data should complete without error."""
        record = self._seed_redirect(slug="exception-test")

        resp = client.post(
            "/adminpanel/slugredirects/bulk_action",
            data={"action": "mark_replace", "selected_ids": [str(record.id)]},
        )

        assert resp.status_code == 302
