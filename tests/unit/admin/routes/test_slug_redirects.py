"""Tests for src/main_app/adminpanel/routes/slug_redirects.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from flask import Blueprint, Flask

from src.main_app.admin.routes.slug_redirects import (
    SlugFuncs,
    SlugRedirectsRoutes,
)


class TestEditSlugRedirect:
    """Direct tests for the _edit_slug_redirect module-level function."""

    def test_with_found_record(self, monkeypatch):
        """_edit_slug_redirect should pass the record to the template."""
        record = MagicMock()
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.get_slug_redirect_by_id",
            MagicMock(return_value=record),
        )
        mock_render = MagicMock(return_value="rendered")
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.render_template",
            mock_render,
        )

        result = SlugFuncs().edit_slug_redirect(1)

        mock_render.assert_called_once_with("admins/slug_redirects/edit.html", record=record, error=None)
        assert result == "rendered"

    def test_with_not_found_record(self, monkeypatch):
        """_edit_slug_redirect should pass an error when the record is missing."""
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.get_slug_redirect_by_id",
            MagicMock(return_value=None),
        )
        mock_render = MagicMock(return_value="rendered")
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.render_template",
            mock_render,
        )

        result = SlugFuncs().edit_slug_redirect(999)

        mock_render.assert_called_once_with(
            "admins/slug_redirects/edit.html",
            error="Redirect record not found",
            record=None,
        )
        assert result == "rendered"


class TestSlugRedirectsClass:
    """Tests for the SlugRedirectsRoutes class itself."""

    def test_blueprint_properties(self):
        """SlugRedirectsRoutes should create a Blueprint with the expected name and prefix."""
        instance = SlugRedirectsRoutes(Blueprint("slugredirects", __name__, url_prefix="/slugredirects"))
        assert isinstance(instance.bp, Blueprint)
        assert instance.bp.name == "slugredirects"
        assert instance.bp.url_prefix == "/slugredirects"

    def test_all_routes_registered(self):
        """SlugRedirectsRoutes should register all 5 routes."""
        instance = SlugRedirectsRoutes(Blueprint("slugredirects", __name__, url_prefix="/slugredirects"))
        assert len(instance.bp.deferred_functions) == 5


class TestSlugRedirectsRoutes:
    """Route-level tests using a Flask test client."""

    @pytest.fixture
    def app_with_routes(self, monkeypatch):
        """Build a minimal Flask app with the slug_redirects blueprint and a mocked admin_required."""
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.admin_required",
            lambda f: f,
        )

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.config["TESTING"] = True

        admin_bp = Blueprint("adminpanel", __name__, url_prefix="/adminpanel")
        admin_bp.register_blueprint(
            SlugRedirectsRoutes(Blueprint("slugredirects", __name__, url_prefix="/slugredirects")).bp
        )
        app.register_blueprint(admin_bp)

        return app

    @pytest.fixture
    def client(self, app_with_routes):
        """Test client bound to the minimal app."""
        return app_with_routes.test_client()

    # ── dashboard (GET /) ────────────────────────────────────────────────

    def test_dashboard_lists_records(self, client, monkeypatch):
        """Dashboard should list all slug redirect records."""
        mock_records = [MagicMock(), MagicMock()]
        mock_records[0].should_be_replaced = True
        mock_records[1].should_be_replaced = False
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.list_slug_redirects",
            MagicMock(return_value=mock_records),
        )
        mock_render = MagicMock(return_value="dashboard")
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.render_template",
            mock_render,
        )

        resp = client.get("/adminpanel/slugredirects/")

        assert resp.status_code == 200
        mock_render.assert_called_once_with(
            "admins/slug_redirects/list.html",
            records=mock_records,
            total=2,
            total_should_be_replaced=1,
            total_should_not_be_replaced=1,
        )

    # ── edit (GET /<id>/edit) ────────────────────────────────────────────

    def test_edit_get_found(self, client, monkeypatch):
        """GET /<id>/edit should render the edit form with the record."""
        record = MagicMock()
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.get_slug_redirect_by_id",
            MagicMock(return_value=record),
        )
        mock_render = MagicMock(return_value="edit_page")
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.render_template",
            mock_render,
        )

        resp = client.get("/adminpanel/slugredirects/1/edit")

        assert resp.status_code == 200
        mock_render.assert_called_once_with("admins/slug_redirects/edit.html", record=record, error=None)

    def test_edit_get_not_found(self, client, monkeypatch):
        """GET /<id>/edit for a missing record should render with an error."""
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.get_slug_redirect_by_id",
            MagicMock(return_value=None),
        )
        mock_render = MagicMock(return_value="error_page")
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.render_template",
            mock_render,
        )

        resp = client.get("/adminpanel/slugredirects/999/edit")

        assert resp.status_code == 200
        mock_render.assert_called_once_with(
            "admins/slug_redirects/edit.html",
            error="Redirect record not found",
            record=None,
        )

    # ── update (POST /update) ────────────────────────────────────────────

    def test_update_success(self, client, monkeypatch):
        """POST /update with valid data should update and redirect."""
        mock_update = MagicMock(return_value=MagicMock())
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.update_slug_redirect",
            mock_update,
        )

        resp = client.post(
            "/adminpanel/slugredirects/update",
            data={"id": 1, "should_be_replaced": "on"},
        )

        mock_update.assert_called_once_with(1, {"should_be_replaced": True})
        assert resp.status_code == 302

    def test_update_missing_id(self, client, monkeypatch):
        """POST /update without an id should not call the service and redirect."""
        mock_update = MagicMock()
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.update_slug_redirect",
            mock_update,
        )

        resp = client.post(
            "/adminpanel/slugredirects/update",
            data={"should_be_replaced": "on"},
        )

        mock_update.assert_not_called()
        assert resp.status_code == 302

    def test_update_not_found(self, client, monkeypatch):
        """POST /update when update_slug_redirect returns None should redirect."""
        mock_update = MagicMock(return_value=None)
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.update_slug_redirect",
            mock_update,
        )

        resp = client.post(
            "/adminpanel/slugredirects/update",
            data={"id": 999, "should_be_replaced": "on"},
        )

        mock_update.assert_called_once_with(999, {"should_be_replaced": True})
        assert resp.status_code == 302

    def test_update_with_from_popup(self, client, monkeypatch):
        """POST /update with from_popup=1 should render popup_action.html."""
        mock_update = MagicMock(return_value=MagicMock())
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.update_slug_redirect",
            mock_update,
        )
        mock_render = MagicMock(return_value="popup")
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.render_template",
            mock_render,
        )

        resp = client.post(
            "/adminpanel/slugredirects/update",
            data={"id": 1, "should_be_replaced": "on", "from_popup": "1"},
        )

        mock_update.assert_called_once_with(1, {"should_be_replaced": True})
        mock_render.assert_called_once_with("admins/popup_action.html")
        assert resp.status_code == 200

    # ── delete (POST /<id>/delete) ───────────────────────────────────────

    def test_delete_success(self, client, monkeypatch):
        """POST /<id>/delete should delete and redirect on success."""
        mock_delete = MagicMock(return_value=True)
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.OwidSlugRedirectsService.delete",
            mock_delete,
        )

        resp = client.post("/adminpanel/slugredirects/1/delete")

        mock_delete.assert_called_once_with(1)
        assert resp.status_code == 302

    def test_delete_not_found(self, client, monkeypatch):
        """POST /<id>/delete should redirect when the record is not found."""
        mock_delete = MagicMock(return_value=False)
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.OwidSlugRedirectsService.delete",
            mock_delete,
        )

        resp = client.post("/adminpanel/slugredirects/999/delete")

        mock_delete.assert_called_once_with(999)
        assert resp.status_code == 302

    # ── bulk_action (POST /bulk_action) ──────────────────────────────────

    def test_bulk_mark_replace(self, client, monkeypatch):
        """POST /bulk_action with action=mark_replace should bulk update."""
        mock_bulk = MagicMock()
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.bulk_update_slug_redirects",
            mock_bulk,
        )

        resp = client.post(
            "/adminpanel/slugredirects/bulk_action",
            data={"action": "mark_replace", "selected_ids": [1, 2, 3]},
        )

        mock_bulk.assert_called_once_with([1, 2, 3], {"should_be_replaced": True})
        assert resp.status_code == 302

    def test_bulk_mark_no_replace(self, client, monkeypatch):
        """POST /bulk_action with action=mark_no_replace should set should_be_replaced=False."""
        mock_bulk = MagicMock()
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.bulk_update_slug_redirects",
            mock_bulk,
        )

        resp = client.post(
            "/adminpanel/slugredirects/bulk_action",
            data={"action": "mark_no_replace", "selected_ids": [1]},
        )

        mock_bulk.assert_called_once_with([1], {"should_be_replaced": False})
        assert resp.status_code == 302

    def test_bulk_delete_action(self, client, monkeypatch):
        """POST /bulk_action with action=delete should bulk delete."""
        mock_bulk = MagicMock()
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.bulk_delete_slug_redirects",
            mock_bulk,
        )

        resp = client.post(
            "/adminpanel/slugredirects/bulk_action",
            data={"action": "delete", "selected_ids": [1, 2]},
        )

        mock_bulk.assert_called_once_with([1, 2])
        assert resp.status_code == 302

    def test_bulk_invalid_action(self, client, monkeypatch):
        """POST /bulk_action with an invalid action should not call any service."""
        mock_bulk_update = MagicMock()
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.bulk_update_slug_redirects",
            mock_bulk_update,
        )
        mock_bulk_delete = MagicMock()
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.bulk_delete_slug_redirects",
            mock_bulk_delete,
        )

        resp = client.post(
            "/adminpanel/slugredirects/bulk_action",
            data={"action": "invalid", "selected_ids": [1]},
        )

        mock_bulk_update.assert_not_called()
        mock_bulk_delete.assert_not_called()
        assert resp.status_code == 302

    def test_bulk_no_items_selected(self, client, monkeypatch):
        """POST /bulk_action without selected_ids should not call any service."""
        mock_bulk = MagicMock()
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.bulk_update_slug_redirects",
            mock_bulk,
        )

        resp = client.post(
            "/adminpanel/slugredirects/bulk_action",
            data={"action": "mark_replace"},
        )

        mock_bulk.assert_not_called()
        assert resp.status_code == 302

    def test_bulk_action_exception(self, client, monkeypatch):
        """POST /bulk_action should handle exceptions gracefully."""
        mock_bulk = MagicMock(side_effect=Exception("DB error"))
        monkeypatch.setattr(
            "src.main_app.admin.routes.slug_redirects.bulk_update_slug_redirects",
            mock_bulk,
        )

        resp = client.post(
            "/adminpanel/slugredirects/bulk_action",
            data={"action": "mark_replace", "selected_ids": [1]},
        )

        mock_bulk.assert_called_once_with([1], {"should_be_replaced": True})
        assert resp.status_code == 302
