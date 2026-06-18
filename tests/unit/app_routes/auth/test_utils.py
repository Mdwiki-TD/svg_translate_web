"""Tests for authentication utilities and decorators."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from flask import Flask, g, session

from src.main_app.app_routes.auth import utils as auth_utils


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    import types

    fake_settings = types.SimpleNamespace(
        cookie=types.SimpleNamespace(name="auth_cookie"),
    )
    monkeypatch.setattr("src.main_app.app_routes.auth.utils.settings", fake_settings)


class TestLoadUser:
    def test_returns_current_user_when_set(self, app: Flask) -> None:
        with app.test_request_context():
            g._current_user = "alice"
            assert auth_utils.load_user() == "alice"

    def test_returns_none_when_not_set(self, app: Flask) -> None:
        with app.test_request_context():
            assert auth_utils.load_user() is None


class TestResolveUserId:
    def test_int_returns_same(self) -> None:
        assert auth_utils._resolve_user_id(42) == 42

    def test_valid_string_returns_int(self) -> None:
        assert auth_utils._resolve_user_id("42") == 42

    def test_none_returns_none(self) -> None:
        assert auth_utils._resolve_user_id(None) is None

    def test_invalid_string_returns_none(self) -> None:
        assert auth_utils._resolve_user_id("not-a-number") is None


class TestLoadLoggedInUser:
    def test_short_circuits_when_g_user_exists(self, app: Flask) -> None:
        with app.test_request_context():
            g._current_user = "existing"
            auth_utils.load_logged_in_user()
            assert g._current_user == "existing"

    def test_from_session_uid(self, app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_user = MagicMock(username="alice")
        monkeypatch.setattr(
            "src.main_app.app_routes.auth.utils.AuthUserService.get_authenticated_user",
            lambda uid: mock_user,
        )
        with app.test_request_context():
            session["uid"] = 42
            auth_utils.load_logged_in_user()
            assert g._current_user is mock_user

    def test_session_resolve_fails_pops_keys(self, app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.main_app.app_routes.auth.utils._resolve_user_id",
            lambda uid: None,
        )
        with app.test_request_context():
            session["uid"] = "bad"
            session["username"] = "tester"
            auth_utils.load_logged_in_user()
            assert g._current_user is None
            assert "uid" not in session
            assert "username" not in session

    def test_fallback_to_cookie_sets_session(self, app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.main_app.app_routes.auth.utils.extract_user_id",
            lambda token: 99,
        )
        mock_user = MagicMock(username="bob")
        monkeypatch.setattr(
            "src.main_app.app_routes.auth.utils.AuthUserService.get_authenticated_user",
            lambda uid: mock_user,
        )
        with app.test_request_context(environ_overrides={"HTTP_COOKIE": "auth_cookie=signed-token"}):
            auth_utils.load_logged_in_user()
            assert g._current_user is mock_user
            assert session.get("uid") == 99

    def test_cookie_extraction_returns_none(self, app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.main_app.app_routes.auth.utils.extract_user_id",
            lambda token: None,
        )
        with app.test_request_context(environ_overrides={"HTTP_COOKIE": "auth_cookie=bad-token"}):
            auth_utils.load_logged_in_user()
            assert g._current_user is None
            assert session.get("uid") is None

    def test_no_user_id_anywhere(self, app: Flask) -> None:
        with app.test_request_context():
            auth_utils.load_logged_in_user()
            assert g._current_user is None

    def test_updates_session_username_when_different(self, app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_user = MagicMock(username="new-name")
        monkeypatch.setattr(
            "src.main_app.app_routes.auth.utils.AuthUserService.get_authenticated_user",
            lambda uid: mock_user,
        )
        with app.test_request_context():
            session["uid"] = 1
            session["username"] = "old-name"
            auth_utils.load_logged_in_user()
            assert session["username"] == "new-name"

    def test_does_not_update_session_username_when_same(self, app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_user = MagicMock(username="alice")
        monkeypatch.setattr(
            "src.main_app.app_routes.auth.utils.AuthUserService.get_authenticated_user",
            lambda uid: mock_user,
        )
        with app.test_request_context():
            session["uid"] = 1
            session["username"] = "alice"
            auth_utils.load_logged_in_user()
            assert session["username"] == "alice"

    def test_user_service_returns_none_sets_g_none(self, app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.main_app.app_routes.auth.utils.AuthUserService.get_authenticated_user",
            lambda uid: None,
        )
        with app.test_request_context():
            session["uid"] = 1
            auth_utils.load_logged_in_user()
            assert g._current_user is None


class TestOauthRequired:
    def test_decorator_calls_function_when_user_exists(self, app: Flask) -> None:
        with app.test_request_context():
            g._current_user = "alice"

            @auth_utils.oauth_required
            def dummy():
                return "ok"

            assert dummy() == "ok"

    def test_redirects_to_login_when_user_is_none(self, app: Flask) -> None:
        with app.test_request_context():
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess.clear()

            @auth_utils.oauth_required
            def dummy():
                return "never reached"

            resp = dummy()
            assert resp.status_code == 302
            assert resp.location == "/login"

    def test_sets_post_login_redirect_in_session(self, app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        with app.test_request_context(
            base_url="https://example.com/",
            path="/some/protected/page",
        ):
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess.clear()

            @auth_utils.oauth_required
            def dummy():
                return "never reached"

            dummy()
            assert session["post_login_redirect"] == "https://example.com/some/protected/page"
