"""Tests for OAuth helpers."""

from __future__ import annotations

import types

import pytest

from src.app.app_routes.auth import oauth


@pytest.fixture(autouse=True)
def fake_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    oauth_config = types.SimpleNamespace(
        consumer_key="consumer",
        consumer_secret="secret",
        mw_uri="https://example.com",
        user_agent="agent",
    )
    settings = types.SimpleNamespace(oauth=oauth_config)
    monkeypatch.setattr(oauth, "settings", settings)


def test_get_handshaker(monkeypatch: pytest.MonkeyPatch) -> None:
    created_tokens: list[tuple[str, str]] = []
    created_handshakers: list[tuple[str, object]] = []

    class DummyHandshaker:
        def __init__(self, uri: str, *, consumer_token: object, user_agent: str) -> None:
            created_handshakers.append((uri, consumer_token, user_agent))

    def fake_consumer(key: str, secret: str) -> tuple[str, str]:
        created_tokens.append((key, secret))
        return (key, secret)

    monkeypatch.setattr(oauth.mwoauth, "ConsumerToken", fake_consumer)
    monkeypatch.setattr(oauth.mwoauth, "Handshaker", DummyHandshaker)

    handshaker = oauth.get_handshaker()

    assert isinstance(handshaker, DummyHandshaker)
    assert created_tokens == [("consumer", "secret")]
    assert created_handshakers[0][0] == "https://example.com"
    assert created_handshakers[0][2] == "agent"


def test_get_handshaker_without_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oauth, "settings", types.SimpleNamespace(oauth=None))

    with pytest.raises(RuntimeError):
        oauth.get_handshaker()


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

    monkeypatch.setattr(oauth, "url_for", fake_url_for)
    monkeypatch.setattr(oauth, "get_handshaker", lambda: DummyHandshaker())

    redirect_url, request_token = oauth.start_login("signed-state")

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

    monkeypatch.setattr(oauth, "get_handshaker", lambda: DummyHandshaker())

    access_token, identity = oauth.complete_login("request-token", "oauth=1")

    assert access_token.key == "k"
    assert identity["username"] == "Tester"


def test_complete_login_identity_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyHandshaker:
        def complete(self, token, query_string: str):
            return "token"

        def identify(self, token) -> dict:
            raise ValueError("bad")

    monkeypatch.setattr(oauth, "get_handshaker", lambda: DummyHandshaker())

    with pytest.raises(oauth.OAuthIdentityError) as excinfo:
        oauth.complete_login("request-token", "query")

    assert "MediaWiki" in str(excinfo.value)
    assert isinstance(excinfo.value.original_exception, ValueError)


def test_oauthidentityerror() -> None:
    error = oauth.OAuthIdentityError("message", original_exception=RuntimeError("boom"))

    assert str(error) == "message"
    assert isinstance(error.original_exception, RuntimeError)
