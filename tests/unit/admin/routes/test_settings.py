"""Tests for src/main_app/admin/routes/settings.py.

Uses the full app factory (TestingConfig) with a real SQLite database.
Only the ``admin_required`` auth decorator is bypassed.
"""

from __future__ import annotations

import pytest
from flask import Blueprint, Flask

from src.main_app.admin.routes.settings import (
    SettingsFuncs,
    SettingsRoutes,
    _parse_setting_value,
)
from src.main_app.database.services import SettingsService

# ---------------------------------------------------------------------------
# SettingsRoutes class structure (no DB needed)
# ---------------------------------------------------------------------------


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.func_service = SettingsFuncs()
        self.service = SettingsService()


class TestSettingsRoutesClass(TestSetup):
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


# ---------------------------------------------------------------------------
# Route-level tests (real DB, admin_required bypassed via unwrap)
# ---------------------------------------------------------------------------


class TestSettingsRoutesRoutes(TestSetup):
    """Route-level tests using the session-scoped app with a real SQLite database.

    The ``admin_required`` decorator is applied at app-factory time, so we
    unwrap the view functions per-test, then restore them afterwards.
    """

    SETTINGS_ENDPOINTS = [
        "adminpanel.settings.dashboard",
        "adminpanel.settings.create",
        "adminpanel.settings.update",
    ]

    @pytest.fixture(autouse=True)
    def _unwrap_admin_required(self, mock_app: Flask):
        """Unwrap admin_required on settings endpoints for the duration of each test."""
        originals = {}
        for endpoint in self.SETTINGS_ENDPOINTS:
            fn = mock_app.view_functions.get(endpoint)
            if fn is not None:
                unwrapped = fn
                while hasattr(unwrapped, "__wrapped__"):
                    unwrapped = unwrapped.__wrapped__
                originals[endpoint] = fn
                mock_app.view_functions[endpoint] = unwrapped
        yield
        for endpoint, fn in originals.items():
            mock_app.view_functions[endpoint] = fn

    # ── dashboard (GET /) ────────────────────────────────────────────────

    def test_dashboard_returns_settings(self, mock_app: Flask, mock_client):
        """Dashboard should render with settings from the real DB."""
        with mock_app.app_context():
            self.service.create_setting("foo", "Foo", "boolean", "true")
            self.service.create_setting("bar", "Bar", "integer", "42")

        resp = mock_client.get("/adminpanel/settings/")
        assert resp.status_code == 200

    # ── create (POST /create) ────────────────────────────────────────────

    def test_create_valid_key(self, mock_app: Flask, mock_client):
        """POST /create with valid key, title, and value_type should persist the setting."""
        resp = mock_client.post(
            "/adminpanel/settings/create",
            data={"key": "my_setting", "title": "My Setting", "value_type": "boolean"},
        )
        assert resp.status_code == 302

        with mock_app.app_context():
            record = self.service.get_setting_by_key("my_setting")
            assert record is not None
            assert record.title == "My Setting"
            assert record.value_type == "boolean"

    def test_create_empty_key_shows_error(self, mock_app: Flask, mock_client):
        """POST /create with an empty key should not create a setting."""
        resp = mock_client.post(
            "/adminpanel/settings/create",
            data={"key": "", "title": "My Setting"},
        )
        assert resp.status_code == 302

        with mock_app.app_context():
            assert self.service.get_setting_by_key("") is None

    def test_create_invalid_key_starts_with_number(self, mock_app: Flask, mock_client):
        """POST /create with a key starting with a number should fail validation."""
        resp = mock_client.post(
            "/adminpanel/settings/create",
            data={"key": "1nvalid", "title": "Invalid"},
        )
        assert resp.status_code == 302

        with mock_app.app_context():
            assert self.service.get_setting_by_key("1nvalid") is None

    def test_create_invalid_key_uppercase(self, mock_app: Flask, mock_client):
        """POST /create with uppercase letters in key should fail validation."""
        resp = mock_client.post(
            "/adminpanel/settings/create",
            data={"key": "MY_SETTING", "title": "My Setting"},
        )
        assert resp.status_code == 302

        with mock_app.app_context():
            assert self.service.get_setting_by_key("MY_SETTING") is None

    def test_create_key_already_exists(self, mock_app: Flask, mock_client):
        """POST /create when setting already exists should flash error and redirect."""
        with mock_app.app_context():
            self.service.create_setting("existing", "Existing", "boolean")

        resp = mock_client.post(
            "/adminpanel/settings/create",
            data={"key": "existing", "title": "Existing", "value_type": "boolean"},
        )
        assert resp.status_code == 302

    def test_create_missing_title(self, mock_app: Flask, mock_client):
        """POST /create with key but no title should show 'Key and Title are required'."""
        resp = mock_client.post(
            "/adminpanel/settings/create",
            data={"key": "valid_key", "title": ""},
        )
        assert resp.status_code == 302

        with mock_app.app_context():
            assert self.service.get_setting_by_key("valid_key") is None

    # ── update (POST /update) ────────────────────────────────────────────

    def test_update_success(self, mock_app: Flask, mock_client, monkeypatch):
        """POST /update with no failed keys should show success flash."""
        monkeypatch.setattr(
            "src.main_app.admin.routes.settings.SettingsFuncs.settings_update_form",
            lambda self, request_form: ([], []),
        )

        resp = mock_client.post("/adminpanel/settings/update", data={})
        assert resp.status_code == 302

    def test_update_with_deleted_keys(self, mock_app: Flask, mock_client, monkeypatch):
        """POST /update with deleted keys should show both 'Deleted' and 'Settings updated'."""
        monkeypatch.setattr(
            "src.main_app.admin.routes.settings.SettingsFuncs.settings_update_form",
            lambda self, request_form: ([], ["key_a", "key_b"]),
        )

        resp = mock_client.post("/adminpanel/settings/update", data={})
        assert resp.status_code == 302

    def test_update_with_failed_keys(self, mock_app: Flask, mock_client, monkeypatch):
        """POST /update with failed keys should show error flash."""
        monkeypatch.setattr(
            "src.main_app.admin.routes.settings.SettingsFuncs.settings_update_form",
            lambda self, request_form: (["bad_key"], []),
        )

        resp = mock_client.post("/adminpanel/settings/update", data={})
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# settings_update_form (real DB)
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("mock_app")
class TestSettingsUpdateForm(TestSetup):
    """Tests for settings_update_form using real DB."""

    def _seed_setting(self, app: Flask, key: str, value_type: str, value: str) -> None:
        with app.app_context():
            self.service.create_setting(key, key.replace("_", " ").title(), value_type, value)

    def test_processes_boolean_value(self, mock_app: Flask):
        self._seed_setting(mock_app, "test_bool", "boolean", "false")

        request_form = {"setting_test_bool": "on"}
        failed, deleted = self.func_service.settings_update_form(request_form)

        assert failed == []
        assert deleted == []

        with mock_app.app_context():
            record = self.service.get_setting_by_key("test_bool")
            assert record is not None
            assert record.value == "true"

    def test_processes_integer_value(self, mock_app: Flask):
        self._seed_setting(mock_app, "test_int", "integer", "0")

        request_form = {"setting_test_int": "42"}
        failed, deleted = self.func_service.settings_update_form(request_form)

        assert failed == []
        assert deleted == []

        with mock_app.app_context():
            record = self.service.get_setting_by_key("test_int")
            assert record is not None
            assert record.value == "42"

    def test_handles_delete_action(self, mock_app: Flask):
        self._seed_setting(mock_app, "test_key", "string", "val")

        request_form = {"delete_test_key": "on"}
        failed, deleted = self.func_service.settings_update_form(request_form)

        assert failed == []
        assert deleted == ["test_key"]

        with mock_app.app_context():
            assert self.service.get_setting_by_key("test_key") is None

    def test_collects_failed_keys_on_error(self, mock_app: Flask, monkeypatch: pytest.MonkeyPatch):
        self._seed_setting(mock_app, "test_key", "string", "val")

        def fail_update(*args, **kwargs):
            return False

        monkeypatch.setattr(
            "src.main_app.admin.routes.settings.SettingsService.update_setting",
            fail_update,
        )

        request_form = {"setting_test_key": "new_val"}
        failed, deleted = self.func_service.settings_update_form(request_form)

        assert deleted == []
        assert "test_key" in failed

    def test_skips_when_form_key_not_in_request_form(self, mock_app: Flask):
        self._seed_setting(mock_app, "test_key", "string", "val")

        request_form = {"other_key": "value"}
        failed, deleted = self.func_service.settings_update_form(request_form)

        assert failed == []
        assert deleted == []

        # Value should be unchanged
        with mock_app.app_context():
            record = self.service.get_setting_by_key("test_key")
            assert record is not None
            assert record.value == "val"


# ---------------------------------------------------------------------------
# _parse_setting_value (pure function — no DB)
# ---------------------------------------------------------------------------


class TestParseSettingValue(TestSetup):
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
