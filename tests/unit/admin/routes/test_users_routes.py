"""Unit tests for src/main_app/adminpanel/routes/users.py."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import pytest
from flask import Blueprint, Flask

from src.main_app.admin.routes.users import UsersRoutes
from src.main_app.db.services import UsersService


@dataclass
class MockUsersDeps:
    flash: MagicMock = field(default_factory=MagicMock)
    render_template: MagicMock = field(default_factory=MagicMock)
    url_for: MagicMock = field(default_factory=MagicMock)
    redirect: MagicMock = field(default_factory=MagicMock)


@pytest.fixture
def mock_deps(monkeypatch: pytest.MonkeyPatch) -> MockUsersDeps:
    deps = MockUsersDeps()
    monkeypatch.setattr("src.main_app.admin.routes.users.render_template", deps.render_template)
    monkeypatch.setattr("src.main_app.admin.routes.users.flash", deps.flash)
    monkeypatch.setattr("src.main_app.admin.routes.users.url_for", deps.url_for)
    monkeypatch.setattr("src.main_app.admin.routes.users.redirect", deps.redirect)

    deps.render_template.return_value = "rendered"
    deps.url_for.return_value = "/adminpanel/users/"
    deps.redirect.return_value = "redirect_response"

    return deps


@pytest.fixture
def users_service() -> UsersService:
    return UsersService()


@pytest.fixture
def seeded_users(users_service: UsersService) -> list[int]:
    alice = users_service.create_user("alice")
    bob = users_service.create_user("bob")
    return [alice.user_id, bob.user_id]


class TestDashboard:
    def test_with_users(self, mock_deps: MockUsersDeps, seeded_users) -> None:
        routes = UsersRoutes(Blueprint("test", __name__))
        result = routes.dashboard()

        mock_deps.render_template.assert_called_once()
        _args, kwargs = mock_deps.render_template.call_args
        assert len(kwargs["users"]) == 2
        assert kwargs["total_users"] == 2
        assert result == "rendered"

    def test_with_0_users(self, mock_deps: MockUsersDeps) -> None:
        routes = UsersRoutes(Blueprint("test", __name__))
        result = routes.dashboard()

        mock_deps.render_template.assert_called_once()
        _args, kwargs = mock_deps.render_template.call_args
        assert kwargs["users"] == []
        assert kwargs["total_users"] == 0
        assert result == "rendered"


class TestUpdatePermissions:
    """Tests for update_can_run_jobs and update_can_run_bg_jobs.

    These route methods access ``request.form`` so we push a request
    context via ``mock_app.test_request_context()`` before calling them.
    """

    @pytest.fixture
    def request_context(self, mock_app: Flask):
        with mock_app.test_request_context(method="POST", data={}):
            yield

    def test_update_can_run_jobs_enable(self, mock_deps, mock_app, seeded_users, users_service) -> None:
        user_id = seeded_users[0]
        with mock_app.test_request_context(method="POST", data={"can_run_jobs": "1"}):
            routes = UsersRoutes(Blueprint("test", __name__))
            result = routes.update_can_run_jobs(user_id)

        mock_deps.flash.assert_called_once()
        assert "permissions updated" in mock_deps.flash.call_args[0][0]
        mock_deps.url_for.assert_called_once_with("adminpanel.users.dashboard")
        mock_deps.redirect.assert_called_once_with("/adminpanel/users/")
        assert result == "redirect_response"

        record = users_service.get_user(user_id)
        assert record.can_run_jobs == 1

    def test_update_can_run_jobs_disable(self, mock_deps, mock_app, seeded_users, users_service) -> None:
        user_id = seeded_users[0]
        with mock_app.test_request_context(method="POST", data={"can_run_jobs": "0"}):
            routes = UsersRoutes(Blueprint("test", __name__))
            result = routes.update_can_run_jobs(user_id)

        mock_deps.flash.assert_called_once()
        assert "permissions updated" in mock_deps.flash.call_args[0][0]
        assert result == "redirect_response"

        record = users_service.get_user(user_id)
        assert record.can_run_jobs == 0

    def test_update_can_run_jobs_default_disable(self, mock_deps, mock_app, seeded_users, users_service) -> None:
        user_id = seeded_users[0]
        with mock_app.test_request_context(method="POST", data={}):
            routes = UsersRoutes(Blueprint("test", __name__))
            result = routes.update_can_run_jobs(user_id)

        mock_deps.flash.assert_called_once()
        assert "permissions updated" in mock_deps.flash.call_args[0][0]
        assert result == "redirect_response"

        record = users_service.get_user(user_id)
        assert record.can_run_jobs == 0

    def test_update_can_run_jobs_lookup_error(self, mock_deps, mock_app) -> None:
        with mock_app.test_request_context(method="POST", data={}):
            routes = UsersRoutes(Blueprint("test", __name__))
            result = routes.update_can_run_jobs(999)

        mock_deps.flash.assert_called_once_with("User with id 999 was not found", "warning")
        mock_deps.url_for.assert_called_once_with("adminpanel.users.dashboard")
        mock_deps.redirect.assert_called_once_with("/adminpanel/users/")
        assert result == "redirect_response"

    def test_update_can_run_bg_jobs_enable(self, mock_deps, mock_app, seeded_users, users_service) -> None:
        user_id = seeded_users[0]
        with mock_app.test_request_context(method="POST", data={"can_run_bg_jobs": "1"}):
            routes = UsersRoutes(Blueprint("test", __name__))
            result = routes.update_can_run_bg_jobs(user_id)

        mock_deps.flash.assert_called_once()
        assert "permissions updated" in mock_deps.flash.call_args[0][0]
        assert result == "redirect_response"

        record = users_service.get_user(user_id)
        assert record.can_run_bg_jobs == 1

    def test_update_can_run_bg_jobs_lookup_error(self, mock_deps, mock_app) -> None:
        with mock_app.test_request_context(method="POST", data={}):
            routes = UsersRoutes(Blueprint("test", __name__))
            result = routes.update_can_run_bg_jobs(999)

        mock_deps.flash.assert_called_once_with("User with id 999 was not found", "warning")
        mock_deps.url_for.assert_called_once_with("adminpanel.users.dashboard")
        mock_deps.redirect.assert_called_once_with("/adminpanel/users/")
        assert result == "redirect_response"


class TestUsersRoutesClass:
    def test_blueprint_properties(self) -> None:
        instance = UsersRoutes(Blueprint("users", __name__, url_prefix="/users"))
        assert isinstance(instance.bp, Blueprint)
        assert instance.bp.name == "users"
        assert instance.bp.url_prefix == "/users"

    def test_all_routes_registered(self) -> None:
        instance = UsersRoutes(Blueprint("users", __name__, url_prefix="/users"))
        assert len(instance.bp.deferred_functions) == 3
