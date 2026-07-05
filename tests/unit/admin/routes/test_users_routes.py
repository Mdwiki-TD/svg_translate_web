"""Unit tests for src/main_app/admin/routes/users.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from flask import Blueprint, Flask

from src.main_app.admin.routes.users import (
    UsersRoutes,
    _dashboard,
    _update_can_run_bg_jobs,
    _update_can_run_jobs,
)
from src.main_app.db.exceptions import UserNotFoundError


class TestDashboard:
    """Direct tests for _dashboard()."""

    def test_with_users(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_users = [MagicMock(username="alice"), MagicMock(username="bob")]
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.list_users",
            lambda: mock_users,
        )
        mock_render = MagicMock(return_value="rendered")
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.render_template",
            mock_render,
        )

        result = _dashboard()

        mock_render.assert_called_once_with(
            "admins/users.html",
            users=mock_users,
            total_users=2,
        )
        assert result == "rendered"

    def test_with_0_users(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.list_users",
            list,
        )
        mock_render = MagicMock(return_value="rendered")
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.render_template",
            mock_render,
        )

        result = _dashboard()

        mock_render.assert_called_once_with(
            "admins/users.html",
            users=[],
            total_users=0,
        )
        assert result == "rendered"

    def test_empty_list_on_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_flash = MagicMock()
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.flash",
            mock_flash,
        )
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.list_users",
            MagicMock(side_effect=Exception("DB error")),
        )
        mock_render = MagicMock(return_value="rendered")
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.render_template",
            mock_render,
        )

        result = _dashboard()

        mock_flash.assert_called_once_with("Error listing users", "error")
        mock_render.assert_called_once_with(
            "admins/users.html",
            users=[],
            total_users=0,
        )
        assert result == "rendered"


@pytest.mark.parametrize("toggle_func_name", ["toggle_can_run_jobs", "toggle_can_run_bg_jobs"])
class TestUpdatePermissions:
    """Parametrized direct tests shared by _update_can_run_jobs and _update_can_run_bg_jobs."""

    def _call_target(self, func_name: str, user_id: int, desired: int) -> str:
        if func_name == "toggle_can_run_jobs":
            return _update_can_run_jobs(user_id, desired)
        return _update_can_run_bg_jobs(user_id, desired)

    def test_success(self, monkeypatch: pytest.MonkeyPatch, toggle_func_name: str) -> None:
        record = MagicMock(username="testuser")
        monkeypatch.setattr(
            f"src.main_app.admin.routes.users.{toggle_func_name}",
            MagicMock(return_value=record),
        )
        mock_flash = MagicMock()
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.flash",
            mock_flash,
        )
        mock_url_for = MagicMock(return_value="/admin/users/")
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.url_for",
            mock_url_for,
        )
        mock_redirect = MagicMock(return_value="redirect_response")
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.redirect",
            mock_redirect,
        )

        result = self._call_target(toggle_func_name, 1, 1)

        mock_flash.assert_called_once_with("User 'testuser' permissions updated.", "success")
        mock_url_for.assert_called_once_with("admin.users.dashboard")
        mock_redirect.assert_called_once_with("/admin/users/")
        assert result == "redirect_response"

    def test_lookup_error(self, monkeypatch: pytest.MonkeyPatch, toggle_func_name: str) -> None:
        monkeypatch.setattr(
            f"src.main_app.admin.routes.users.{toggle_func_name}",
            MagicMock(side_effect=UserNotFoundError("User with id 999 was not found")),
        )
        mock_flash = MagicMock()
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.flash",
            mock_flash,
        )
        mock_url_for = MagicMock(return_value="/admin/users/")
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.url_for",
            mock_url_for,
        )
        mock_redirect = MagicMock(return_value="redirect_response")
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.redirect",
            mock_redirect,
        )

        result = self._call_target(toggle_func_name, 999, 1)

        mock_flash.assert_called_once_with("User with id 999 was not found", "warning")
        mock_url_for.assert_called_once_with("admin.users.dashboard")
        mock_redirect.assert_called_once_with("/admin/users/")
        assert result == "redirect_response"

    def test_generic_exception(self, monkeypatch: pytest.MonkeyPatch, toggle_func_name: str) -> None:
        monkeypatch.setattr(
            f"src.main_app.admin.routes.users.{toggle_func_name}",
            MagicMock(side_effect=Exception("Unexpected error")),
        )
        mock_flash = MagicMock()
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.flash",
            mock_flash,
        )
        mock_url_for = MagicMock(return_value="/admin/users/")
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.url_for",
            mock_url_for,
        )
        mock_redirect = MagicMock(return_value="redirect_response")
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.redirect",
            mock_redirect,
        )

        result = self._call_target(toggle_func_name, 1, 0)

        mock_flash.assert_called_once_with(
            "Unable to update user permissions. Please try again.",
            "danger",
        )
        mock_url_for.assert_called_once_with("admin.users.dashboard")
        mock_redirect.assert_called_once_with("/admin/users/")
        assert result == "redirect_response"


class TestUsersRoutesClass:
    """Tests for the UsersRoutes class itself."""

    def test_blueprint_properties(self) -> None:
        instance = UsersRoutes()
        assert isinstance(instance.bp, Blueprint)
        assert instance.bp.name == "users"
        assert instance.bp.url_prefix == "/users"

    def test_all_routes_registered(self) -> None:
        instance = UsersRoutes()
        assert len(instance.bp.deferred_functions) == 3


class TestUsersRoutesRoutes:
    """Route-level tests using a Flask test client."""

    @pytest.fixture
    def app_with_routes(self, monkeypatch: pytest.MonkeyPatch) -> Flask:
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.admin_required",
            lambda f: f,
        )

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.config["TESTING"] = True

        admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
        admin_bp.register_blueprint(UsersRoutes().bp)
        app.register_blueprint(admin_bp)

        return app

    @pytest.fixture
    def client(self, app_with_routes: Flask):
        return app_with_routes.test_client()

    def test_dashboard_get(self, client, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_users = [MagicMock(username="alice")]
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.list_users",
            MagicMock(return_value=mock_users),
        )
        mock_render = MagicMock(return_value="dashboard")
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.render_template",
            mock_render,
        )

        resp = client.get("/admin/users/")

        assert resp.status_code == 200
        mock_render.assert_called_once_with(
            "admins/users.html",
            users=mock_users,
            total_users=1,
        )

    def test_dashboard_get_exception(self, client, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.list_users",
            MagicMock(side_effect=Exception("DB error")),
        )
        mock_render = MagicMock(return_value="dashboard")
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.render_template",
            mock_render,
        )

        resp = client.get("/admin/users/")

        assert resp.status_code == 200
        mock_render.assert_called_once_with(
            "admins/users.html",
            users=[],
            total_users=0,
        )

    def test_post_can_run_jobs_enable(self, client, monkeypatch: pytest.MonkeyPatch) -> None:
        record = MagicMock(username="testuser")
        mock_toggle = MagicMock(return_value=record)
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.toggle_can_run_jobs",
            mock_toggle,
        )

        resp = client.post("/admin/users/1/can_run_jobs", data={"can_run_jobs": "1"})

        mock_toggle.assert_called_once_with(1, 1)
        assert resp.status_code == 302

    def test_post_can_run_jobs_disable(self, client, monkeypatch: pytest.MonkeyPatch) -> None:
        record = MagicMock(username="testuser")
        mock_toggle = MagicMock(return_value=record)
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.toggle_can_run_jobs",
            mock_toggle,
        )

        resp = client.post("/admin/users/1/can_run_jobs", data={"can_run_jobs": "0"})

        mock_toggle.assert_called_once_with(1, 0)
        assert resp.status_code == 302

    def test_post_can_run_jobs_default_disable(self, client, monkeypatch: pytest.MonkeyPatch) -> None:
        record = MagicMock(username="testuser")
        mock_toggle = MagicMock(return_value=record)
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.toggle_can_run_jobs",
            mock_toggle,
        )

        resp = client.post("/admin/users/1/can_run_jobs", data={})

        mock_toggle.assert_called_once_with(1, 0)
        assert resp.status_code == 302

    def test_post_can_run_bg_jobs_enable(self, client, monkeypatch: pytest.MonkeyPatch) -> None:
        record = MagicMock(username="testuser")
        mock_toggle = MagicMock(return_value=record)
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.toggle_can_run_bg_jobs",
            mock_toggle,
        )

        resp = client.post("/admin/users/1/can_run_bg_jobs", data={"can_run_bg_jobs": "1"})

        mock_toggle.assert_called_once_with(1, 1)
        assert resp.status_code == 302

    def test_post_can_run_bg_jobs_disable(self, client, monkeypatch: pytest.MonkeyPatch) -> None:
        record = MagicMock(username="testuser")
        mock_toggle = MagicMock(return_value=record)
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.toggle_can_run_bg_jobs",
            mock_toggle,
        )

        resp = client.post("/admin/users/1/can_run_bg_jobs", data={"can_run_bg_jobs": "0"})

        mock_toggle.assert_called_once_with(1, 0)
        assert resp.status_code == 302

    def test_post_can_run_bg_jobs_default_disable(self, client, monkeypatch: pytest.MonkeyPatch) -> None:
        record = MagicMock(username="testuser")
        mock_toggle = MagicMock(return_value=record)
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.toggle_can_run_bg_jobs",
            mock_toggle,
        )

        resp = client.post("/admin/users/1/can_run_bg_jobs", data={})

        mock_toggle.assert_called_once_with(1, 0)
        assert resp.status_code == 302
