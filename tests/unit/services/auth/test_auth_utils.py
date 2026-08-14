"""Tests for authentication utilities and decorators."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from flask import Flask, g, session

from src.main_app.services.auth import utils as auth_utils


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> None:

    fake_settings = SimpleNamespace(
        cookie=SimpleNamespace(name="auth_cookie"),
    )
    monkeypatch.setattr("src.main_app.services.auth.utils.settings", fake_settings)


class TestLoadUser:
    def test_returns_current_user_when_set(self, mock_app: Flask) -> None:
        with mock_app.test_request_context():
            g._current_user = "alice"
            assert auth_utils.get_current_user() == "alice"

    def test_returns_none_when_not_set(self, mock_app: Flask) -> None:
        with mock_app.test_request_context():
            assert auth_utils.get_current_user() is None


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

    def test_short_circuits_when_g_user_exists(self, mock_app: Flask) -> None:
        with mock_app.test_request_context():
            g._current_user = "existing"
            auth_utils.set_logged_in_user()
            assert g._current_user == "existing"

    def test_from_session_uid(self, mock_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_user = MagicMock(username="alice")
        monkeypatch.setattr(
            "src.main_app.services.auth.utils.TokenManager.get_authenticated_user",
            lambda _, uid: mock_user,
        )
        with mock_app.test_request_context():
            session["uid"] = 42
            auth_utils.set_logged_in_user()
            assert g._current_user is mock_user

    def test_session_resolve_fails_pops_keys(self, mock_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.main_app.services.auth.utils._resolve_user_id",
            lambda uid: None,
        )
        with mock_app.test_request_context():
            session["uid"] = "bad"
            session["username"] = "tester"
            auth_utils.set_logged_in_user()
            assert g._current_user is None
            assert "uid" not in session
            assert "username" not in session

    def test_fallback_to_cookie_sets_session(self, mock_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.main_app.services.auth.utils.extract_user_id",
            lambda token: 99,
        )
        mock_user = MagicMock(username="bob")
        monkeypatch.setattr(
            "src.main_app.services.auth.utils.TokenManager.get_authenticated_user",
            lambda _, uid: mock_user,
        )
        with mock_app.test_request_context(environ_overrides={"HTTP_COOKIE": "auth_cookie=signed-token"}):
            auth_utils.set_logged_in_user()
            assert g._current_user is mock_user
            assert session.get("uid") == 99

    def test_cookie_extraction_returns_none(self, mock_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.main_app.services.auth.utils.extract_user_id",
            lambda token: None,
        )
        with mock_app.test_request_context(environ_overrides={"HTTP_COOKIE": "auth_cookie=bad-token"}):
            auth_utils.set_logged_in_user()
            assert g._current_user is None
            assert session.get("uid") is None

    def test_no_user_id_anywhere(self, mock_app: Flask) -> None:
        with mock_app.test_request_context():
            auth_utils.set_logged_in_user()
            assert g._current_user is None

    def test_updates_session_username_when_different(self, mock_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_user = MagicMock(username="new-name")
        monkeypatch.setattr(
            "src.main_app.services.auth.utils.TokenManager.get_authenticated_user",
            lambda _, uid: mock_user,
        )
        with mock_app.test_request_context():
            session["uid"] = 1
            session["username"] = "old-name"
            auth_utils.set_logged_in_user()
            assert session["username"] == "new-name"

    def test_does_not_update_session_username_when_same(self, mock_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_user = MagicMock(username="alice")
        monkeypatch.setattr(
            "src.main_app.services.auth.utils.TokenManager.get_authenticated_user",
            lambda _, uid: mock_user,
        )
        with mock_app.test_request_context():
            session["uid"] = 1
            session["username"] = "alice"
            auth_utils.set_logged_in_user()
            assert session["username"] == "alice"

    def test_user_service_returns_none_sets_g_none(self, mock_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.main_app.services.auth.utils.TokenManager.get_authenticated_user",
            lambda _, uid: None,
        )
        with mock_app.test_request_context():
            session["uid"] = 1
            auth_utils.set_logged_in_user()
            assert g._current_user is None
