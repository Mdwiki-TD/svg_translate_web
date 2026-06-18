"""Tests for src/main_app/app_routes/admin_routes/settings.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from flask import Blueprint, Flask

from src.main_app.app_routes.admin_routes.settings import SettingsRoutes


class TestSettingsRoutesClass:
    """Tests for the SettingsRoutes class itself."""

    def test_blueprint_properties(self):
        """SettingsRoutes should create a Blueprint with the expected name and prefix."""
        instance = SettingsRoutes()
        assert isinstance(instance.bp, Blueprint)
        assert instance.bp.name == "settings"
        assert instance.bp.url_prefix == "/settings"

    def test_all_routes_registered(self):
        """SettingsRoutes should register all 3 routes."""
        instance = SettingsRoutes()
        assert len(instance.bp.deferred_functions) == 3


class TestSettingsRoutesRoutes:
    """Route-level tests using a Flask test client."""

    @pytest.fixture
    def app_with_routes(self, monkeypatch):
        """Build a minimal Flask app with the settings blueprint and a mocked admin_required."""
        monkeypatch.setattr(
            "src.main_app.app_routes.admin_routes.settings.admin_required",
            lambda f: f,
        )

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.config["TESTING"] = True

        admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
        admin_bp.register_blueprint(SettingsRoutes().bp)
        app.register_blueprint(admin_bp)

        return app

    @pytest.fixture
    def client(self, app_with_routes):
        """Test client bound to the minimal app."""
        return app_with_routes.test_client()

    # ── dashboard (GET /) ────────────────────────────────────────────────

    def test_dashboard_returns_settings(self, client, monkeypatch):
        """Dashboard should render the template with all settings."""
        mock_settings = [{"key": "foo", "value": "true"}, {"key": "bar", "value": "42"}]
        monkeypatch.setattr(
            "src.main_app.app_routes.admin_routes.settings.get_all_settings_raw",
            MagicMock(return_value=mock_settings),
        )
        mock_render = MagicMock(return_value="dashboard")
        monkeypatch.setattr(
            "src.main_app.app_routes.admin_routes.settings.render_template",
            mock_render,
        )

        resp = client.get("/admin/settings/")

        assert resp.status_code == 200
        mock_render.assert_called_once_with("admins/settings.html", settings_list=mock_settings)

    # ── create (POST /create) ────────────────────────────────────────────

    def test_create_valid_key(self, client, monkeypatch):
        """POST /create with valid key, title, and value_type should call create_setting."""
        mock_create = MagicMock(return_value=True)
        monkeypatch.setattr(
            "src.main_app.app_routes.admin_routes.settings.create_setting",
            mock_create,
        )

        resp = client.post(
            "/admin/settings/create",
            data={"key": "my_setting", "title": "My Setting", "value_type": "boolean"},
        )

        mock_create.assert_called_once_with("my_setting", "My Setting", "boolean")
        assert resp.status_code == 302

    def test_create_empty_key_shows_error(self, client, monkeypatch):
        """POST /create with an empty key should not call create_setting and redirect."""
        mock_create = MagicMock()
        monkeypatch.setattr(
            "src.main_app.app_routes.admin_routes.settings.create_setting",
            mock_create,
        )

        resp = client.post(
            "/admin/settings/create",
            data={"key": "", "title": "My Setting"},
        )

        mock_create.assert_not_called()
        assert resp.status_code == 302

    def test_create_invalid_key_starts_with_number(self, client, monkeypatch):
        """POST /create with a key starting with a number should show validation error."""
        mock_create = MagicMock()
        monkeypatch.setattr(
            "src.main_app.app_routes.admin_routes.settings.create_setting",
            mock_create,
        )

        resp = client.post(
            "/admin/settings/create",
            data={"key": "1nvalid", "title": "Invalid"},
        )

        mock_create.assert_not_called()
        assert resp.status_code == 302

    def test_create_invalid_key_uppercase(self, client, monkeypatch):
        """POST /create with uppercase letters in key should show validation error."""
        mock_create = MagicMock()
        monkeypatch.setattr(
            "src.main_app.app_routes.admin_routes.settings.create_setting",
            mock_create,
        )

        resp = client.post(
            "/admin/settings/create",
            data={"key": "MY_SETTING", "title": "My Setting"},
        )

        mock_create.assert_not_called()
        assert resp.status_code == 302

    def test_create_key_already_exists(self, client, monkeypatch):
        """POST /create when create_setting returns False should show 'already exists' flash."""
        mock_create = MagicMock(return_value=False)
        monkeypatch.setattr(
            "src.main_app.app_routes.admin_routes.settings.create_setting",
            mock_create,
        )

        resp = client.post(
            "/admin/settings/create",
            data={"key": "existing", "title": "Existing"},
        )

        mock_create.assert_called_once_with("existing", "Existing", "boolean")
        assert resp.status_code == 302

    def test_create_missing_title(self, client, monkeypatch):
        """POST /create with key but no title should show 'Key and Title are required'."""
        mock_create = MagicMock()
        monkeypatch.setattr(
            "src.main_app.app_routes.admin_routes.settings.create_setting",
            mock_create,
        )

        resp = client.post(
            "/admin/settings/create",
            data={"key": "valid_key", "title": ""},
        )

        mock_create.assert_not_called()
        assert resp.status_code == 302

    # ── update (POST /update) ────────────────────────────────────────────

    def test_update_success(self, client, monkeypatch):
        """POST /update with no failed keys should show success flash."""
        monkeypatch.setattr(
            "src.main_app.app_routes.admin_routes.settings.settings_update_form",
            MagicMock(return_value=([], [])),
        )

        resp = client.post("/admin/settings/update", data={})

        assert resp.status_code == 302

    def test_update_with_deleted_keys(self, client, monkeypatch):
        """POST /update with deleted keys should show both 'Deleted' and 'Settings updated'."""
        monkeypatch.setattr(
            "src.main_app.app_routes.admin_routes.settings.settings_update_form",
            MagicMock(return_value=([], ["key_a", "key_b"])),
        )

        resp = client.post("/admin/settings/update", data={})

        assert resp.status_code == 302

    def test_update_with_failed_keys(self, client, monkeypatch):
        """POST /update with failed keys should show error flash."""
        monkeypatch.setattr(
            "src.main_app.app_routes.admin_routes.settings.settings_update_form",
            MagicMock(return_value=(["bad_key"], [])),
        )

        resp = client.post("/admin/settings/update", data={})

        assert resp.status_code == 302
