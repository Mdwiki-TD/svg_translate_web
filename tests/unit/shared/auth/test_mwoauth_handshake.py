"""Unit tests for src/main_app/shared/auth/mwoauth_handshake.py."""

from __future__ import annotations

import types
from types import SimpleNamespace

import pytest

from src.main_app.shared.auth import mwoauth_handshake


@pytest.fixture(autouse=True)
def fake_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    oauth_config = types.SimpleNamespace(
        consumer_key="consumer",
        consumer_secret="secret",
        mw_uri="https://example.com",
    )
    settings = types.SimpleNamespace(
        oauth=oauth_config,
        other=types.SimpleNamespace(
            user_agent="agent",
        ),
    )
    monkeypatch.setattr("src.main_app.shared.auth.mwoauth_handshake.settings", settings)


def test_get_handshaker(monkeypatch: pytest.MonkeyPatch) -> None:
    created_tokens: list[tuple[str, str]] = []
    created_handshakers: list[tuple[str, object]] = []

    class DummyHandshaker:
        def __init__(self, uri: str, *, consumer_token: object, user_agent: str) -> None:
            created_handshakers.append((uri, consumer_token, user_agent))

    def fake_consumer(key: str, secret: str) -> tuple[str, str]:
        created_tokens.append((key, secret))
        return (key, secret)

    monkeypatch.setattr(mwoauth_handshake.mwoauth, "ConsumerToken", fake_consumer)
    monkeypatch.setattr(mwoauth_handshake.mwoauth, "Handshaker", DummyHandshaker)

    handshaker = mwoauth_handshake.get_handshaker()

    assert isinstance(handshaker, DummyHandshaker)
    assert created_tokens == [("consumer", "secret")]
    assert created_handshakers[0][0] == "https://example.com"
    assert created_handshakers[0][2] == "agent"


def test_get_handshaker_without_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.main_app.shared.auth.mwoauth_handshake.settings", types.SimpleNamespace(oauth=None))

    with pytest.raises(RuntimeError):
        mwoauth_handshake.get_handshaker()


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

    monkeypatch.setattr("src.main_app.shared.auth.mwoauth_handshake.url_for", fake_url_for)
    monkeypatch.setattr("src.main_app.shared.auth.mwoauth_handshake.get_handshaker", lambda: DummyHandshaker())

    redirect_url, request_token = mwoauth_handshake.start_login("signed-state")

    assert redirect_url == "https://auth"
    assert list(request_token) == ["token", "secret"]
    assert captured_state == ["signed-state"]


def test_complete_login(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyHandshaker:
        def complete(self, token, query_string: str):
            assert token == "request-token"
            assert query_string == "oauth=1"
            return types.SimpleNamespace(key="k", secret="s")

        def identify(self, token) -> dict:
            assert token.key == "k"
            return {"sub": "123", "username": "Tester"}

    monkeypatch.setattr("src.main_app.shared.auth.mwoauth_handshake.get_handshaker", lambda: DummyHandshaker())

    access_token, identity = mwoauth_handshake.complete_login("request-token", "oauth=1")

    assert access_token.key == "k"  # type: ignore
    assert identity["username"] == "Tester"


def test_complete_login_identity_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyHandshaker:
        def complete(self, token, query_string: str):
            return "token"

        def identify(self, token) -> dict:
            raise ValueError("bad")

    monkeypatch.setattr("src.main_app.shared.auth.mwoauth_handshake.get_handshaker", lambda: DummyHandshaker())

    with pytest.raises(mwoauth_handshake.OAuthIdentityError) as excinfo:
        mwoauth_handshake.complete_login("request-token", "query")

    assert "MediaWiki" in str(excinfo.value)
    assert isinstance(excinfo.value.original_exception, ValueError)


def test_oauthidentityerror() -> None:
    error = mwoauth_handshake.OAuthIdentityError("message", original_exception=RuntimeError("boom"))

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
    monkeypatch.setattr(mwoauth_handshake, "mwoauth", StubMWOAuth())
    access_token, identity = mwoauth_handshake.complete_login(("rk", "rs"), "a=1&b=2")
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

    monkeypatch.setattr(mwoauth_handshake, "mwoauth", FailingMWOAuth())
    with pytest.raises(mwoauth_handshake.OAuthIdentityError):
        mwoauth_handshake.complete_login(("rk", "rs"), "x=1")
