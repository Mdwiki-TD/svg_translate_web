"""Tests for authentication utilities and decorators."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from flask import Flask, g, session
from src.main_app.services.auth.current_user_resolver import (
    CurrentUserResolver,
)


class TestLoadUser:
    def test_returns_current_user_when_set(self, mock_app: Flask) -> None:
        with mock_app.test_request_context():
            g._current_user = "alice"
            assert CurrentUserResolver.get_current_user() == "alice"

    def test_returns_none_when_not_set(self, mock_app: Flask) -> None:
        with mock_app.test_request_context():
            assert CurrentUserResolver.get_current_user() is None


class TestResolveUserId:
    def test_int_returns_same(self) -> None:
        assert CurrentUserResolver.resolve_user_id(42) == 42

    def test_valid_string_returns_int(self) -> None:
        assert CurrentUserResolver.resolve_user_id("42") == 42

    def test_none_returns_none(self) -> None:
        assert CurrentUserResolver.resolve_user_id(None) is None

    def test_invalid_string_returns_none(self) -> None:
        assert CurrentUserResolver.resolve_user_id("not-a-number") is None

    def test_unsupported_type_returns_none(self) -> None:
        # Objects without valid __int__ conversion trigger TypeError.
        assert CurrentUserResolver.resolve_user_id(["42"]) is None


class TestLoadLoggedInUser:
    def test_uses_default_cookie_name_from_settings(self, mock_app: Flask) -> None:
        signer = MagicMock()
        signer.extract_user_id.return_value = 7
        mock_user = MagicMock(username="charlie")
        token_manager = MagicMock()
        token_manager.get_authenticated_user.return_value = mock_user

        mock_settings = MagicMock()
        mock_settings.cookie.name = "default_auth_cookie"

        with (
            patch(
                "src.main_app.services.auth.current_user_resolver.get_settings",
                return_value=mock_settings,
            ),
            mock_app.test_request_context(
                environ_overrides={"HTTP_COOKIE": "default_auth_cookie=signed-token"}
            ),
        ):
            CurrentUserResolver(
                signer=signer,
                token_manager=token_manager,
            ).set_logged_in_user()
            assert g._current_user is mock_user
            assert session["uid"] == 7

    def test_short_circuits_when_g_user_exists(self, mock_app: Flask) -> None:
        token_manager = MagicMock()
        with mock_app.test_request_context():
            g._current_user = "existing"
            CurrentUserResolver(token_manager=token_manager).set_logged_in_user()
            assert g._current_user == "existing"
            token_manager.get_authenticated_user.assert_not_called()

    def test_from_session_uid(self, mock_app: Flask) -> None:
        mock_user = MagicMock(username="alice")
        token_manager = MagicMock()
        token_manager.get_authenticated_user.return_value = mock_user

        with mock_app.test_request_context():
            session["uid"] = 42
            CurrentUserResolver(
                token_manager=token_manager,
            ).set_logged_in_user()
            assert g._current_user is mock_user
            token_manager.get_authenticated_user.assert_called_once_with(42)

    def test_session_resolve_fails_pops_keys(self, mock_app: Flask) -> None:
        with mock_app.test_request_context():
            session["uid"] = "bad"
            session["username"] = "tester"
            CurrentUserResolver().set_logged_in_user()
            assert g._current_user is None
            assert "uid" not in session
            assert "username" not in session

    def test_invalid_cookie_uid_pops_session_keys(self, mock_app: Flask) -> None:
        signer = MagicMock()
        signer.extract_user_id.return_value = "not-an-int"

        resolver = CurrentUserResolver(
            signer=signer,
            cookie_name="auth_cookie",
        )
        with mock_app.test_request_context(
            environ_overrides={"HTTP_COOKIE": "auth_cookie=malformed-uid"}
        ):
            session["username"] = "stale-user"
            resolver.set_logged_in_user()
            assert g._current_user is None
            assert "uid" not in session
            assert "username" not in session

    def test_fallback_to_cookie_sets_session(self, mock_app: Flask) -> None:
        signer = MagicMock()
        signer.extract_user_id.return_value = 99
        mock_user = MagicMock(username="bob")

        token_manager = MagicMock()
        token_manager.get_authenticated_user.return_value = mock_user

        resolver = CurrentUserResolver(
            signer=signer,
            token_manager=token_manager,
            cookie_name="auth_cookie",
        )
        with mock_app.test_request_context(
            environ_overrides={"HTTP_COOKIE": "auth_cookie=signed-token"}
        ):
            resolver.set_logged_in_user()
            assert g._current_user is mock_user
            assert session.get("uid") == 99
            assert session.get("username") == "bob"

    def test_cookie_extraction_returns_none(self, mock_app: Flask) -> None:
        signer = MagicMock()
        signer.extract_user_id.return_value = None

        with mock_app.test_request_context(
            environ_overrides={"HTTP_COOKIE": "auth_cookie=bad-token"}
        ):
            CurrentUserResolver(
                signer=signer,
                cookie_name="auth_cookie",
            ).set_logged_in_user()
            assert g._current_user is None
            assert session.get("uid") is None

    def test_no_user_id_anywhere(self, mock_app: Flask) -> None:
        token_manager = MagicMock()
        with mock_app.test_request_context():
            CurrentUserResolver(
                token_manager=token_manager,
                cookie_name="auth_cookie",
            ).set_logged_in_user()
            assert g._current_user is None
            token_manager.get_authenticated_user.assert_not_called()

    def test_updates_session_username_when_different(self, mock_app: Flask) -> None:
        mock_user = MagicMock(username="new-name")

        token_manager = MagicMock()
        token_manager.get_authenticated_user.return_value = mock_user

        with mock_app.test_request_context():
            session["uid"] = 1
            session["username"] = "old-name"
            CurrentUserResolver(
                token_manager=token_manager,
            ).set_logged_in_user()
            assert session["username"] == "new-name"

    def test_does_not_update_session_username_when_same(self, mock_app: Flask) -> None:
        mock_user = MagicMock(username="alice")
        token_manager = MagicMock()
        token_manager.get_authenticated_user.return_value = mock_user

        with mock_app.test_request_context():
            session["uid"] = 1
            session["username"] = "alice"
            CurrentUserResolver(
                token_manager=token_manager,
            ).set_logged_in_user()
            assert session["username"] == "alice"

    def test_user_service_returns_none_sets_g_none(self, mock_app: Flask) -> None:
        token_manager = MagicMock()
        token_manager.get_authenticated_user.return_value = None

        with mock_app.test_request_context():
            session["uid"] = 1
            session["username"] = "alice"
            CurrentUserResolver(
                token_manager=token_manager,
            ).set_logged_in_user()
            assert g._current_user is None
            # Username stays untouched when no DB record is returned.
            assert session["username"] == "alice"
