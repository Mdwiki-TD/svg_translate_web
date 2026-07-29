"""Tests for src/main_app/adminpanel/routes/settings.py."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Blueprint
from werkzeug.datastructures import ImmutableMultiDict

from src.main_app.admin.routes.settings import SettingsRoutes, _parse_setting_value, settings_update_form
from src.main_app.db.services import SettingsService


@pytest.fixture(autouse=True)
def _fake_admin_user(monkeypatch):
    """Fake an authenticated admin user for all tests in this module."""
    admin_user = SimpleNamespace(username="test_admin", is_active_admin=True)
    monkeypatch.setattr("src.main_app.admin.decorators.load_user", lambda: admin_user)


@pytest.fixture
def client(mock_app):
    """Test client bound to mock_app."""
    return mock_app.test_client()


class TestSettingsRoutesClass:
    """Tests for the SettingsRoutes class itself."""

    def test_blueprint_properties(self):
        """SettingsRoutes should create a Blueprint with the expected name and prefix."""
        instance = SettingsRoutes(Blueprint("settings", __name__, url_prefix="/settings"))
        assert isinstance(instance.bp, Blueprint)
        assert instance.bp.name == "settings"
        assert instance.bp.url_prefix == "/settings"

    def test_all_routes_registered(self):
        """SettingsRoutes should register all 3 routes."""
        instance = SettingsRoutes(Blueprint("settings", __name__, url_prefix="/settings"))
        assert len(instance.bp.deferred_functions) == 3


class TestSettingsRoutesRoutes:
    """Route-level tests using mock_app's test client with real DB/services."""

    def _seed_setting(self, key: str = "test_key", title: str = "Test Setting", value_type: str = "boolean", value=None):
        """Seed a setting record via the real service."""
        service = SettingsService()
        service.create_setting(key, title, value_type, value)
        return service.get_setting_by_key(key)

    # ── dashboard (GET /) ────────────────────────────────────────────────

    def test_dashboard_returns_settings(self, client):
        """Dashboard should render the template with all settings."""
        self._seed_setting(key="foo", title="Foo", value_type="boolean", value=True)
        self._seed_setting(key="bar", title="Bar", value_type="integer", value=42)

        resp = client.get("/adminpanel/settings/")

        assert resp.status_code == 200
        html = resp.data.decode()
        assert "foo" in html
        assert "bar" in html

    # ── create (POST /create) ────────────────────────────────────────────

    def test_create_valid_key(self, client):
        """POST /create with valid key, title, and value_type should create the setting."""
        resp = client.post(
            "/adminpanel/settings/create",
            data={"key": "my_setting", "title": "My Setting", "value_type": "boolean"},
        )

        assert resp.status_code == 302
        assert SettingsService().get_setting_by_key("my_setting") is not None

    def test_create_empty_key_shows_error(self, client):
        """POST /create with an empty key should not create a setting."""
        resp = client.post(
            "/adminpanel/settings/create",
            data={"key": "", "title": "My Setting"},
        )

        assert resp.status_code == 302

    def test_create_invalid_key_starts_with_number(self, client):
        """POST /create with a key starting with a number should show validation error."""
        resp = client.post(
            "/adminpanel/settings/create",
            data={"key": "1nvalid", "title": "Invalid"},
        )

        assert resp.status_code == 302

    def test_create_invalid_key_uppercase(self, client):
        """POST /create with uppercase letters in key should show validation error."""
        resp = client.post(
            "/adminpanel/settings/create",
            data={"key": "MY_SETTING", "title": "My Setting"},
        )

        assert resp.status_code == 302

    def test_create_key_already_exists(self, client):
        """POST /create when key already exists should show 'already exists' flash."""
        self._seed_setting(key="existing", title="Existing")

        resp = client.post(
            "/adminpanel/settings/create",
            data={"key": "existing", "title": "Existing"},
        )

        assert resp.status_code == 302

    def test_create_missing_title(self, client):
        """POST /create with key but no title should show 'Key and Title are required'."""
        resp = client.post(
            "/adminpanel/settings/create",
            data={"key": "valid_key", "title": ""},
        )

        assert resp.status_code == 302

    # ── update (POST /update) ────────────────────────────────────────────

    def test_update_success(self, client):
        """POST /update with no failed keys should show success flash."""
        resp = client.post("/adminpanel/settings/update", data={})

        assert resp.status_code == 302

    def test_update_with_deleted_keys(self, client):
        """POST /update with deleted keys should show both 'Deleted' and 'Settings updated'."""
        self._seed_setting(key="to_delete", title="Delete Me")

        resp = client.post(
            "/adminpanel/settings/update",
            data={"delete_to_delete": "on"},
        )

        assert resp.status_code == 302
        assert SettingsService().get_setting_by_key("to_delete") is None

    def test_update_with_failed_keys(self, client):
        """POST /update with failed keys should show error flash."""
        self._seed_setting(key="fail_key", title="Fail Key", value_type="integer")

        resp = client.post(
            "/adminpanel/settings/update",
            data={"setting_fail_key": "not_a_number"},
        )

        assert resp.status_code == 302


class TestSettingsUpdateForm:
    """Tests for settings_update_form with real services."""

    def test_processes_boolean_value(self):
        """Boolean setting should be toggled from form data."""
        service = SettingsService()
        service.create_setting("test_bool", "Test Bool", "boolean", False)

        request_form = ImmutableMultiDict({"setting_test_bool": "on"})
        failed, deleted = settings_update_form(request_form)

        assert failed == []
        assert deleted == []
        setting = service.get_setting_by_key("test_bool")
        assert setting.value == "true"

    def test_processes_integer_value(self):
        """Integer setting should be updated from form data."""
        service = SettingsService()
        service.create_setting("test_int", "Test Int", "integer", 0)

        request_form = ImmutableMultiDict({"setting_test_int": "42"})
        failed, deleted = settings_update_form(request_form)

        assert failed == []
        assert deleted == []
        setting = service.get_setting_by_key("test_int")
        assert setting.value == "42"

    def test_handles_delete_action(self):
        """Delete action should remove the setting."""
        service = SettingsService()
        service.create_setting("test_key", "Test Key", "string", "val")

        request_form = ImmutableMultiDict({"delete_test_key": "on"})
        failed, deleted = settings_update_form(request_form)

        assert failed == []
        assert deleted == ["test_key"]
        assert service.get_setting_by_key("test_key") is None

    def test_collects_failed_keys_on_error(self):
        """Invalid integer value should add key to failed list."""
        service = SettingsService()
        service.create_setting("test_key", "Test Key", "integer", 0)

        request_form = ImmutableMultiDict({"setting_test_key": "not_a_number"})
        failed, deleted = settings_update_form(request_form)

        assert deleted == []
        assert "test_key" in failed

    def test_skips_when_form_key_not_in_request_form(self):
        """Setting not present in form should not be updated."""
        service = SettingsService()
        service.create_setting("test_key", "Test Key", "string", "original")

        request_form = ImmutableMultiDict({"other_key": "value"})
        failed, deleted = settings_update_form(request_form)

        assert failed == []
        assert deleted == []
        setting = service.get_setting_by_key("test_key")
        assert setting.value == "original"


class TestParseSettingValue:
    """Tests for _parse_setting_value."""

    def test_boolean_on(self):
        assert _parse_setting_value("boolean", "on") == (True, True)

    def test_boolean_off(self):
        assert _parse_setting_value("boolean", "off") == (False, True)

    def test_boolean_empty(self):
        assert _parse_setting_value("boolean", "") == (False, True)

    def test_boolean_other(self):
        assert _parse_setting_value("boolean", "true") == (False, True)

    def test_integer_valid(self):
        assert _parse_setting_value("integer", "42") == (42, True)

    def test_integer_negative(self):
        assert _parse_setting_value("integer", "-10") == (-10, True)

    def test_integer_invalid(self):
        assert _parse_setting_value("integer", "abc") == (0, False)

    def test_integer_empty(self):
        assert _parse_setting_value("integer", "") == (0, False)

    def test_string(self):
        assert _parse_setting_value("string", "hello") == ("hello", True)

    def test_unknown_type(self):
        assert _parse_setting_value("unknown", "raw") == ("raw", True)
