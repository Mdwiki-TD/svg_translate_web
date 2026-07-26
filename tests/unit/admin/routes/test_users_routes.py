"""Unit tests for src/main_app/adminpanel/routes/users.py."""

from __future__ import annotations

from dataclasses import dataclass, field
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
from src.main_app.db.services import UsersService


@dataclass
class MockUsersDeps:
    """Typed bundle of all mocked users route dependencies."""

    flash: MagicMock = field(default_factory=MagicMock)
    render_template: MagicMock = field(default_factory=MagicMock)
    url_for: MagicMock = field(default_factory=MagicMock)
    redirect: MagicMock = field(default_factory=MagicMock)
    list_users: MagicMock = field(default_factory=MagicMock)
    toggle_can_run_jobs: MagicMock = field(default_factory=MagicMock)
    toggle_can_run_bg_jobs: MagicMock = field(default_factory=MagicMock)


@pytest.fixture
def mock_deps(monkeypatch: pytest.MonkeyPatch) -> MockUsersDeps:
    """Patch all users route dependencies and return a typed bundle."""

    deps = MockUsersDeps()
    monkeypatch.setattr("src.main_app.admin.routes.users.render_template", deps.render_template)
    monkeypatch.setattr("src.main_app.admin.routes.users.flash", deps.flash)
    monkeypatch.setattr("src.main_app.admin.routes.users.url_for", deps.url_for)
    monkeypatch.setattr("src.main_app.admin.routes.users.redirect", deps.redirect)
    monkeypatch.setattr(UsersService, "list_users", deps.list_users)
    monkeypatch.setattr(UsersService, "toggle_can_run_jobs", deps.toggle_can_run_jobs)
    monkeypatch.setattr(UsersService, "toggle_can_run_bg_jobs", deps.toggle_can_run_bg_jobs)

    deps.render_template.return_value = "rendered"
    deps.url_for.return_value = "/adminpanel/users/"
    deps.redirect.return_value = "redirect_response"

    return deps


class TestDashboard:
    """Direct tests for _dashboard()."""

    def test_with_users(self, mock_deps: MockUsersDeps) -> None:
        mock_users = [MagicMock(username="alice"), MagicMock(username="bob")]
        mock_deps.list_users.return_value = mock_users

        result = _dashboard()

        mock_deps.render_template.assert_called_once_with(
            "admins/users.html",
            users=mock_users,
            total_users=2,
        )
        assert result == "rendered"

    def test_with_0_users(self, mock_deps: MockUsersDeps) -> None:
        mock_deps.list_users.return_value = []

        result = _dashboard()

        mock_deps.render_template.assert_called_once_with(
            "admins/users.html",
            users=[],
            total_users=0,
        )
        assert result == "rendered"

    def test_empty_list_on_exception(self, mock_deps: MockUsersDeps) -> None:
        mock_deps.list_users.side_effect = Exception("DB error")

        result = _dashboard()

        mock_deps.flash.assert_called_once_with("Error listing users", "error")
        mock_deps.render_template.assert_called_once_with(
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

    def test_success(self, mock_deps: MockUsersDeps, toggle_func_name: str) -> None:
        record = MagicMock(username="testuser")
        toggle_mock = getattr(mock_deps, toggle_func_name)
        toggle_mock.return_value = record

        result = self._call_target(toggle_func_name, 1, 1)

        mock_deps.flash.assert_called_once_with("User 'testuser' permissions updated.", "success")
        mock_deps.url_for.assert_called_once_with("adminpanel.users.dashboard")
        mock_deps.redirect.assert_called_once_with("/adminpanel/users/")
        assert result == "redirect_response"

    def test_lookup_error(self, mock_deps: MockUsersDeps, toggle_func_name: str) -> None:
        toggle_mock = getattr(mock_deps, toggle_func_name)
        toggle_mock.side_effect = UserNotFoundError("User with id 999 was not found")

        result = self._call_target(toggle_func_name, 999, 1)

        mock_deps.flash.assert_called_once_with("User with id 999 was not found", "warning")
        mock_deps.url_for.assert_called_once_with("adminpanel.users.dashboard")
        mock_deps.redirect.assert_called_once_with("/adminpanel/users/")
        assert result == "redirect_response"

    def test_generic_exception(self, mock_deps: MockUsersDeps, toggle_func_name: str) -> None:
        toggle_mock = getattr(mock_deps, toggle_func_name)
        toggle_mock.side_effect = Exception("Unexpected error")

        result = self._call_target(toggle_func_name, 1, 0)

        mock_deps.flash.assert_called_once_with(
            "Unable to update user permissions. Please try again.",
            "danger",
        )
        mock_deps.url_for.assert_called_once_with("adminpanel.users.dashboard")
        mock_deps.redirect.assert_called_once_with("/adminpanel/users/")
        assert result == "redirect_response"


class TestUsersRoutesClass:
    """Tests for the UsersRoutes class itself."""

    def test_blueprint_properties(self) -> None:
        instance = UsersRoutes(Blueprint("users", __name__, url_prefix="/users"))
        assert isinstance(instance.bp, Blueprint)
        assert instance.bp.name == "users"
        assert instance.bp.url_prefix == "/users"

    def test_all_routes_registered(self) -> None:
        instance = UsersRoutes(Blueprint("users", __name__, url_prefix="/users"))
        assert len(instance.bp.deferred_functions) == 3


class TestUsersRoutesRoutes:
    """Route-level tests using a Flask test client."""

    @pytest.fixture(autouse=True)
    def _restore_flask(self, monkeypatch: pytest.MonkeyPatch, mock_deps: MockUsersDeps) -> None:
        """Re-patch redirect/url_for with real Flask; keep render_template mocked."""
        from flask import redirect as _real_redirect
        from flask import url_for as _real_url_for

        _m = "src.main_app.admin.routes.users"
        monkeypatch.setattr("src.main_app.admin.routes.users.redirect", _real_redirect)
        monkeypatch.setattr("src.main_app.admin.routes.users.url_for", _real_url_for)

    @pytest.fixture
    def app_with_routes(self, monkeypatch: pytest.MonkeyPatch) -> Flask:
        monkeypatch.setattr(
            "src.main_app.admin.routes.users.admin_required",
            lambda f: f,
        )

        app = Flask(__name__)
        app.secret_key = "test-secret"
        app.config["TESTING"] = True

        admin_bp = Blueprint("adminpanel", __name__, url_prefix="/adminpanel")
        admin_bp.register_blueprint(UsersRoutes(Blueprint("users", __name__, url_prefix="/users")).bp)
        app.register_blueprint(admin_bp)

        return app

    @pytest.fixture
    def client(self, app_with_routes: Flask):
        return app_with_routes.test_client()

    def test_dashboard_get(self, client, mock_deps: MockUsersDeps) -> None:
        mock_users = [MagicMock(username="alice")]
        mock_deps.list_users.return_value = mock_users

        resp = client.get("/adminpanel/users/")

        assert resp.status_code == 200
        mock_deps.render_template.assert_called_once_with(
            "admins/users.html",
            users=mock_users,
            total_users=1,
        )

    def test_dashboard_get_exception(self, client, mock_deps: MockUsersDeps) -> None:
        mock_deps.list_users.side_effect = Exception("DB error")

        resp = client.get("/adminpanel/users/")

        assert resp.status_code == 200
        mock_deps.render_template.assert_called_once_with(
            "admins/users.html",
            users=[],
            total_users=0,
        )

    def test_post_can_run_jobs_enable(self, client, mock_deps: MockUsersDeps) -> None:
        record = MagicMock(username="testuser")
        mock_deps.toggle_can_run_jobs.return_value = record

        resp = client.post("/adminpanel/users/1/can_run_jobs", data={"can_run_jobs": "1"})

        mock_deps.toggle_can_run_jobs.assert_called_once_with(1, 1)
        assert resp.status_code == 302

    def test_post_can_run_jobs_disable(self, client, mock_deps: MockUsersDeps) -> None:
        record = MagicMock(username="testuser")
        mock_deps.toggle_can_run_jobs.return_value = record

        resp = client.post("/adminpanel/users/1/can_run_jobs", data={"can_run_jobs": "0"})

        mock_deps.toggle_can_run_jobs.assert_called_once_with(1, 0)
        assert resp.status_code == 302

    def test_post_can_run_jobs_default_disable(self, client, mock_deps: MockUsersDeps) -> None:
        record = MagicMock(username="testuser")
        mock_deps.toggle_can_run_jobs.return_value = record

        resp = client.post("/adminpanel/users/1/can_run_jobs", data={})

        mock_deps.toggle_can_run_jobs.assert_called_once_with(1, 0)
        assert resp.status_code == 302

    def test_post_can_run_bg_jobs_enable(self, client, mock_deps: MockUsersDeps) -> None:
        record = MagicMock(username="testuser")
        mock_deps.toggle_can_run_bg_jobs.return_value = record

        resp = client.post("/adminpanel/users/1/can_run_bg_jobs", data={"can_run_bg_jobs": "1"})

        mock_deps.toggle_can_run_bg_jobs.assert_called_once_with(1, 1)
        assert resp.status_code == 302

    def test_post_can_run_bg_jobs_disable(self, client, mock_deps: MockUsersDeps) -> None:
        record = MagicMock(username="testuser")
        mock_deps.toggle_can_run_bg_jobs.return_value = record

        resp = client.post("/adminpanel/users/1/can_run_bg_jobs", data={"can_run_bg_jobs": "0"})

        mock_deps.toggle_can_run_bg_jobs.assert_called_once_with(1, 0)
        assert resp.status_code == 302

    def test_post_can_run_bg_jobs_default_disable(self, client, mock_deps: MockUsersDeps) -> None:
        record = MagicMock(username="testuser")
        mock_deps.toggle_can_run_bg_jobs.return_value = record

        resp = client.post("/adminpanel/users/1/can_run_bg_jobs", data={})

        mock_deps.toggle_can_run_bg_jobs.assert_called_once_with(1, 0)
        assert resp.status_code == 302
