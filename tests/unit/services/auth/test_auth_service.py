"""Unit tests for auth_service."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.services.auth import auth_service
from src.main_app.services.auth.auth_service import (
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
        patch("src.main_app.services.auth.auth_service.OAuthService.complete_login") as m_login,
        patch("src.main_app.services.auth.auth_service.TokenManager.save_token") as m_save,
    ):
        m_login.return_value = (MagicMock(key="k", secret="s"), {"username": "user123"})
        m_save.return_value = MagicMock(username="user123")

        res = complete_oauth_callback("req_token", "query")
        assert res.username == "user123"


def test_complete_oauth_callback_no_username():
    with patch("src.main_app.services.auth.auth_service.OAuthService.complete_login") as m_login:
        m_login.return_value = (MagicMock(key="k", secret="s"), {})
        with pytest.raises(OAuthCallbackError, match="Missing username"):
            complete_oauth_callback("req_token", "query")


def test_complete_oauth_callback_save_fail():
    with (
        patch("src.main_app.services.auth.auth_service.OAuthService.complete_login") as m_login,
        patch("src.main_app.services.auth.auth_service.TokenManager.save_token") as m_save,
    ):
        m_login.return_value = (MagicMock(key="k", secret="s"), {"username": "user123"})
        m_save.return_value = None

        with pytest.raises(OAuthCallbackError, match="Failed to process user credentials"):
            complete_oauth_callback("req_token", "query")


@pytest.fixture(autouse=True)
def fake_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    oauth_config = SimpleNamespace(
        consumer_key="consumer",
        consumer_secret="secret",
        mw_uri="https://example.com",
    )
    settings = SimpleNamespace(
        oauth=oauth_config,
        other=SimpleNamespace(
            user_agent="agent",
        ),
    )
    monkeypatch.setattr("src.main_app.services.auth.auth_service.settings", settings)


def test_get_handshaker(monkeypatch: pytest.MonkeyPatch) -> None:
    created_tokens: list[tuple[str, str]] = []
    created_handshakers: list[tuple[str, object]] = []

    class DummyHandshaker:
        def __init__(self, uri: str, *, consumer_token: object, user_agent: str) -> None:
            created_handshakers.append((uri, consumer_token, user_agent))

    def fake_consumer(key: str, secret: str) -> tuple[str, str]:
        created_tokens.append((key, secret))
        return (key, secret)

    monkeypatch.setattr(auth_service.mwoauth, "ConsumerToken", fake_consumer)
    monkeypatch.setattr(auth_service.mwoauth, "Handshaker", DummyHandshaker)

    handshaker = auth_service.get_handshaker()

    assert isinstance(handshaker, DummyHandshaker)
    assert created_tokens == [("consumer", "secret")]
    assert created_handshakers[0][0] == "https://example.com"
    assert created_handshakers[0][2] == "agent"


def test_get_handshaker_without_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.main_app.services.auth.auth_service.settings", SimpleNamespace(oauth=None))

    with pytest.raises(RuntimeError):
        auth_service.get_handshaker()


def test_start_login(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_state: list[str] = []

    def fake_url_for(endpoint: str, **params: str) -> str:
        assert endpoint == "auth.callback"
        captured_state.append(params["state"])
        return "https://host/callback"

    class DummyHandshaker:
        def initiate(self, *, callback: str):
            assert callback == "https://host/callback"
            return "https://auth", ("token", "secret")

    monkeypatch.setattr("src.main_app.services.auth.auth_service.url_for", fake_url_for)
    monkeypatch.setattr("src.main_app.services.auth.auth_service.OAuthService.get_handshaker", lambda: DummyHandshaker())

    redirect_url, request_token = auth_service.start_login("signed-state")

    assert redirect_url == "https://auth"
    assert list(request_token) == ["token", "secret"]
    assert captured_state == ["signed-state"]


def test_complete_login(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyHandshaker:
        def complete(self, token, query_string: str):
            assert token == "request-token"
            assert query_string == "oauth=1"
            return SimpleNamespace(key="k", secret="s")

        def identify(self, token) -> dict:
            assert token.key == "k"
            return {"sub": "123", "username": "Tester"}

    monkeypatch.setattr("src.main_app.services.auth.auth_service.OAuthService.get_handshaker", lambda: DummyHandshaker())

    access_token, identity = auth_service.complete_login("request-token", "oauth=1")

    assert access_token.key == "k"  # type: ignore
    assert identity["username"] == "Tester"


def test_complete_login_identity_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyHandshaker:
        def complete(self, token, query_string: str):
            return "token"

        def identify(self, token) -> dict:
            raise ValueError("bad")

    monkeypatch.setattr("src.main_app.services.auth.auth_service.OAuthService.get_handshaker", lambda: DummyHandshaker())

    with pytest.raises(auth_service.OAuthIdentityError) as excinfo:
        auth_service.complete_login("request-token", "query")

    assert "MediaWiki" in str(excinfo.value)
    assert isinstance(excinfo.value.original_exception, ValueError)


def test_oauthidentityerror() -> None:
    error = auth_service.OAuthIdentityError("message", original_exception=RuntimeError("boom"))

    assert str(error) == "message"
    assert isinstance(error.original_exception, RuntimeError)


class StubConsumerToken:
    def __init__(self, key, secret):
        self.key = key

        self.secret = secret


class StubHandshaker:
    def __init__(self, mw_uri, consumer_token=None, user_agent=None):
        self.mw_uri = mw_uri
        self.consumer_token = consumer_token
        self.user_agent = user_agent

    def initiate(self, callback=None):
        return "https://example.org/redirect", ("req-key", "req-secret")

    def complete(self, _request_token, _query_string):
        return ("acc-key", "acc-secret")

    def identify(self, _access_token):
        return {"username": "Alice", "sub": 123}


class StubMWOAuth(SimpleNamespace):
    def __init__(self):
        super().__init__(ConsumerToken=StubConsumerToken, Handshaker=StubHandshaker)


def test_complete_login_returns_access_and_identity(monkeypatch):
    monkeypatch.setattr(auth_service, "mwoauth", StubMWOAuth())
    access_token, identity = auth_service.complete_login(("rk", "rs"), "a=1&b=2")
    assert isinstance(access_token, tuple) and access_token[0] == "acc-key"
    assert identity["username"] == "Alice"


def test_complete_login_raises_identity_error(monkeypatch):
    class FailingHandshaker(StubHandshaker):
        def identify(self, _access_token):
            raise RuntimeError("boom")

    class FailingMWOAuth(StubMWOAuth):
        def __init__(self):
            super().__init__()
            self.Handshaker = FailingHandshaker

    monkeypatch.setattr(auth_service, "mwoauth", FailingMWOAuth())
    with pytest.raises(auth_service.OAuthIdentityError):
        auth_service.complete_login(("rk", "rs"), "x=1")
