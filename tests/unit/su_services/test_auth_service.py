"""Unit tests for auth_service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.su_services.auth_service import (
    OAuthCallbackError,
    complete_oauth_callback,
    extract_token_credentials,
)


def test_extract_token_credentials_object():
    token = MagicMock()
    token.key = "key"
    token.secret = "secret"
    assert extract_token_credentials(token) == ("key", "secret")


def test_extract_token_credentials_sequence():
    token = ["key_seq", "secret_seq"]
    assert extract_token_credentials(token) == ("key_seq", "secret_seq")


def test_extract_token_credentials_fail():
    with pytest.raises(OAuthCallbackError, match="Missing OAuth credentials"):
        extract_token_credentials(None)


def test_complete_oauth_callback_success():
    with (
        patch("src.main_app.su_services.auth_service.complete_login") as m_login,
        patch("src.main_app.su_services.auth_service.AuthUserService.save_and_get_user") as m_save,
    ):
        m_login.return_value = (MagicMock(key="k", secret="s"), {"username": "user123"})
        m_save.return_value = MagicMock(username="user123")

        res = complete_oauth_callback("req_token", "query")
        assert res.username == "user123"


def test_complete_oauth_callback_no_username():
    with patch("src.main_app.su_services.auth_service.complete_login") as m_login:
        m_login.return_value = (MagicMock(key="k", secret="s"), {})
        with pytest.raises(OAuthCallbackError, match="Missing username"):
            complete_oauth_callback("req_token", "query")


def test_complete_oauth_callback_save_fail():
    with (
        patch("src.main_app.su_services.auth_service.complete_login") as m_login,
        patch("src.main_app.su_services.auth_service.AuthUserService.save_and_get_user") as m_save,
    ):
        m_login.return_value = (MagicMock(key="k", secret="s"), {"username": "user123"})
        m_save.return_value = None

        with pytest.raises(OAuthCallbackError, match="Failed to process user credentials"):
            complete_oauth_callback("req_token", "query")
