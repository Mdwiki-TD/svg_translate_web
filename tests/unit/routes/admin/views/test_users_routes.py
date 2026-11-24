"""Unit tests for src/main_app/routes/admin/views/users.py."""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import MagicMock

import pytest
from flask import Blueprint, Flask
from src.main_app.database.services import UsersService
from src.main_app.routes.admin.views.users import (
    UpdateCanRunBgJobsView,
    UpdateCanRunJobsView,
    UsersDashboardView,
    UsersRoutes,
)


@dataclass
class MockUsersDeps:
    flash: MagicMock = field(default_factory=MagicMock)
    render_template: MagicMock = field(default_factory=MagicMock)
    url_for: MagicMock = field(default_factory=MagicMock)
    redirect: MagicMock = field(default_factory=MagicMock)


@pytest.fixture
def mock_deps(monkeypatch: pytest.MonkeyPatch) -> MockUsersDeps:
    deps = MockUsersDeps()
    monkeypatch.setattr("src.main_app.routes.admin.views.users.render_template", deps.render_template)
    monkeypatch.setattr("src.main_app.routes.admin.views.users.flash", deps.flash)
    monkeypatch.setattr("src.main_app.routes.admin.views.users.url_for", deps.url_for)
    monkeypatch.setattr("src.main_app.routes.admin.views.users.redirect", deps.redirect)

    deps.render_template.return_value = "rendered"
    deps.url_for.return_value = "/admin_panel/users/"
    deps.redirect.return_value = "redirect_response"

    return deps


@pytest.fixture
def users_service() -> UsersService:
    return UsersService()


@pytest.fixture
def seeded_users() -> list[int]:
    users_service = UsersService()
    alice = users_service.create_user("alice")
    bob = users_service.create_user("bob")

    assert alice is not None
    assert bob is not None

    return [alice.user_id, bob.user_id]


class TestDashboard:
    def test_with_users(self, mock_deps: MockUsersDeps, seeded_users) -> None:
        routes = UsersRoutes()
        routes.register(Blueprint("test", __name__))
        result = UsersDashboardView().get()

        mock_deps.render_template.assert_called_once()
        _args, kwargs = mock_deps.render_template.call_args
        assert result == "rendered"

        assert kwargs["total_users"] == 2
        assert len(kwargs["users"]) == 2

    def test_with_0_users(self, mock_deps: MockUsersDeps) -> None:
        routes = UsersRoutes()
        routes.register(Blueprint("test", __name__))
        result = UsersDashboardView().get()

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
            routes = UsersRoutes()
            routes.register(Blueprint("test", __name__))
            result = UpdateCanRunJobsView().post(user_id)

        mock_deps.flash.assert_called_once()
        assert "permissions updated" in mock_deps.flash.call_args[0][0]
        mock_deps.url_for.assert_called_once_with("admin_panel.users.dashboard")
        mock_deps.redirect.assert_called_once_with("/admin_panel/users/")
        assert result == "redirect_response"

        record = users_service.get_user(user_id)
        assert record.can_run_jobs == 1

    def test_update_can_run_jobs_disable(self, mock_deps, mock_app, seeded_users, users_service) -> None:
        user_id = seeded_users[0]
        with mock_app.test_request_context(method="POST", data={"can_run_jobs": "0"}):
            routes = UsersRoutes()
            routes.register(Blueprint("test", __name__))
            result = UpdateCanRunJobsView().post(user_id)

        mock_deps.flash.assert_called_once()
        assert "permissions updated" in mock_deps.flash.call_args[0][0]
        assert result == "redirect_response"

        record = users_service.get_user(user_id)
        assert record.can_run_jobs == 0

    def test_update_can_run_jobs_default_disable(self, mock_deps, mock_app, seeded_users, users_service) -> None:
        user_id = seeded_users[0]
        with mock_app.test_request_context(method="POST", data={}):
            routes = UsersRoutes()
            routes.register(Blueprint("test", __name__))
            result = UpdateCanRunJobsView().post(user_id)

        mock_deps.flash.assert_called_once()
        assert "permissions updated" in mock_deps.flash.call_args[0][0]
        assert result == "redirect_response"

        record = users_service.get_user(user_id)
        assert record.can_run_jobs == 0

    def test_update_can_run_jobs_lookup_error(self, mock_deps, mock_app) -> None:
        with mock_app.test_request_context(method="POST", data={}):
            routes = UsersRoutes()
            routes.register(Blueprint("test", __name__))
            result = UpdateCanRunJobsView().post(999)

        mock_deps.flash.assert_called_once_with("User with id 999 was not found", "warning")
        mock_deps.url_for.assert_called_once_with("admin_panel.users.dashboard")
        mock_deps.redirect.assert_called_once_with("/admin_panel/users/")
        assert result == "redirect_response"

    def test_update_can_run_bg_jobs_enable(self, mock_deps, mock_app, seeded_users, users_service) -> None:
        user_id = seeded_users[0]
        with mock_app.test_request_context(method="POST", data={"can_run_bg_jobs": "1"}):
            routes = UsersRoutes()
            routes.register(Blueprint("test", __name__))
            result = UpdateCanRunBgJobsView().post(user_id)

        mock_deps.flash.assert_called_once()
        assert "permissions updated" in mock_deps.flash.call_args[0][0]
        assert result == "redirect_response"

        record = users_service.get_user(user_id)
        assert record.can_run_bg_jobs == 1

    def test_update_can_run_bg_jobs_lookup_error(self, mock_deps, mock_app) -> None:
        with mock_app.test_request_context(method="POST", data={}):
            routes = UsersRoutes()
            routes.register(Blueprint("test", __name__))
            result = UpdateCanRunBgJobsView().post(999)

        mock_deps.flash.assert_called_once_with("User with id 999 was not found", "warning")
        mock_deps.url_for.assert_called_once_with("admin_panel.users.dashboard")
        mock_deps.redirect.assert_called_once_with("/admin_panel/users/")
        assert result == "redirect_response"
