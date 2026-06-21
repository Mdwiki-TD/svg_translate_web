"""
Tests for admin_required decorator.
"""

from __future__ import annotations

import types
from unittest.mock import patch  # , MagicMock

import pytest
from werkzeug.exceptions import Forbidden

from src.main_app.app_routes.admin.decorators import admin_required


class MockUser:
    def __init__(self, username, is_active_admin):
        self.username = username
        self.is_active_admin = is_active_admin


def test_admin_required_redirects_when_not_logged_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.main_app.app_routes.admin.decorators.load_user", lambda: None)
    monkeypatch.setattr("src.main_app.app_routes.admin.decorators.redirect", lambda location: f"redirect:{location}")
    monkeypatch.setattr("src.main_app.app_routes.admin.decorators.url_for", lambda endpoint: f"/{endpoint}")

    @admin_required
    def view() -> str:
        return "ok"

    assert view() == "redirect:/auth.login"


def test_admin_required_blocks_non_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.main_app.app_routes.admin.decorators.load_user",
        lambda: types.SimpleNamespace(username="user", is_active_admin=False),
    )

    class AbortCalled(Exception):  # noqa: N818
        pass

    def fake_abort(code: int) -> None:
        raise AbortCalled(code)

    monkeypatch.setattr("src.main_app.app_routes.admin.decorators.abort", fake_abort)

    @admin_required
    def view() -> str:
        return "ok"

    with pytest.raises(AbortCalled) as excinfo:
        view()

    assert excinfo.value.args[0] == 403


def test_admin_required_allows_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.main_app.app_routes.admin.decorators.load_user",
        lambda: types.SimpleNamespace(username="boss", is_active_admin=True),
    )

    @admin_required
    def view() -> str:
        return "ok"

    assert view() == "ok"


def test_admin_required_not_logged_in():
    """
    Tests that a user who is not logged in is redirected to the login page.
    """

    # A dummy view function
    @admin_required
    def dummy_view():
        return "This should not be returned"

    with (
        patch("src.main_app.app_routes.admin.decorators.load_user", return_value=None),
        patch("src.main_app.app_routes.admin.decorators.redirect") as mock_redirect,
        patch("src.main_app.app_routes.admin.decorators.url_for", return_value="/login") as mock_url_for,
    ):
        response = dummy_view()

        # Check that url_for was called for the login page
        mock_url_for.assert_called_once_with("auth.login")
        # Check that redirect was called with the login page URL
        mock_redirect.assert_called_once_with("/login")
        # Check that the response is the one from redirect
        assert response == mock_redirect.return_value


def test_admin_required_not_admin():
    """
    Tests that a logged-in, non-admin user is denied access with a 403 error.
    """

    # A dummy view function
    @admin_required
    def dummy_view():
        return "This should not be returned"

    # Mock user who is not in the admin list
    mock_user = MockUser(username="testuser", is_active_admin=False)

    with (patch("src.main_app.app_routes.admin.decorators.load_user", return_value=mock_user),):
        # Expect a Forbidden (403) exception to be raised
        with pytest.raises(Forbidden):
            dummy_view()


def test_admin_required_is_admin():
    """
    Tests that a logged-in admin user is granted access.
    """

    # A dummy view function
    @admin_required
    def dummy_view():
        return "success"

    # Mock user who is in the admin list
    mock_user = MockUser(username="admin1", is_active_admin=True)

    with (patch("src.main_app.app_routes.admin.decorators.load_user", return_value=mock_user),):
        # The view should be executed and return its value
        response = dummy_view()
        assert response == "success"
