"""Unit tests for auth_service."""

from __future__ import annotations

from types import SimpleNamespace
from mwoauth import RequestToken

import pytest

from src.main_app.services.auth import auth_service
from src.main_app.services.auth.auth_service import OAuthService


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
        def __init__(self, mw_uri: str, *, consumer_token: object, user_agent: str) -> None:
            created_handshakers.append((mw_uri, consumer_token, user_agent))

    def fake_consumer(key: str, secret: str) -> tuple[str, str]:
        created_tokens.append((key, secret))
        return (key, secret)

    monkeypatch.setattr(auth_service, "ConsumerToken", fake_consumer)
    monkeypatch.setattr(auth_service, "Handshaker", DummyHandshaker)

    handshaker = OAuthService().get_handshaker()

    assert isinstance(handshaker, DummyHandshaker)
    assert created_tokens == [("consumer", "secret")]
    assert created_handshakers[0][0] == "https://example.com"
    assert created_handshakers[0][2] == "agent"


def test_get_handshaker_without_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.main_app.services.auth.auth_service.settings", SimpleNamespace(oauth=None))

    with pytest.raises(RuntimeError):
        OAuthService().get_handshaker()


def test_start_login(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_state: list[str] = []

    class DummyHandshaker:
        def __init__(self, *args, **kwargs) -> None:
            pass
        def initiate(self, *, callback: str):
            assert callback == "https://host/callback?state=signed-state"
            return "https://auth", ("token", "secret")

    monkeypatch.setattr(
        "src.main_app.services.auth.auth_service.Handshaker", lambda self, *args, **kwargs: DummyHandshaker()
    )

    redirect_url, request_token, request_secret = OAuthService().create_authorization_url("https://host/callback?state=signed-state")

    assert redirect_url == "https://auth"
    assert list(request_token) == ["token", "secret"]
    assert captured_state == []


def test_complete_login(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyHandshaker:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def complete(self, token, query_string: str):
            assert token == RequestToken(key='request-token', secret='request-secret')
            assert query_string == "oauth=1"
            return SimpleNamespace(key="k", secret="s")

        def identify(self, token) -> dict:
            assert token.key == "k"
            return {"sub": "123", "username": "Tester"}

    monkeypatch.setattr(
        "src.main_app.services.auth.auth_service.Handshaker", lambda self, *args, **kwargs: DummyHandshaker()
    )

    access_token = OAuthService().fetch_access_token("oauth=1", "request-token", "request-secret")
    identity = OAuthService().identify(access_token)

    assert access_token.key == "k"  # type: ignore
    assert identity["username"] == "Tester"


def test_complete_login_identity_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyHandshaker:
        def __init__(self, *args, **kwargs) -> None:
            pass
        def complete(self, token, query_string: str):
            return "token"

        def identify(self, token) -> dict:
            raise ValueError("bad")

    monkeypatch.setattr(
        "src.main_app.services.auth.auth_service.Handshaker", lambda self, *args, **kwargs: DummyHandshaker()
    )

    with pytest.raises(auth_service.OAuthIdentityError) as excinfo:
        OAuthService().fetch_access_token("query", "request-token", "request-token")

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
    monkeypatch.setattr(auth_service, "Handshaker", StubHandshaker)
    access_token = OAuthService().fetch_access_token("a=1&b=2", "rk", "rs")
    identity = OAuthService().identify(access_token)

    assert isinstance(access_token, tuple) and access_token[0] == "acc-key"
    assert identity["username"] == "Alice"


def test_complete_login_raises_identity_error(monkeypatch):
    class FailingHandshaker(StubHandshaker):
        def identify(self, _access_token):
            raise RuntimeError("boom")

    monkeypatch.setattr(auth_service, "Handshaker", FailingHandshaker)
    with pytest.raises(auth_service.OAuthIdentityError):
        OAuthService().fetch_access_token("x=1", "rk", "rs")
