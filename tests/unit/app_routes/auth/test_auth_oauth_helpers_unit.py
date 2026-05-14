"""Unit tests for OAuth helper functions using a stubbed mwoauth."""

from types import SimpleNamespace

import pytest

from src.main_app.app_routes.auth import oauth as oauth_helpers


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
    monkeypatch.setattr(oauth_helpers, "mwoauth", StubMWOAuth())
    access_token, identity = oauth_helpers.complete_login(("rk", "rs"), "a=1&b=2")
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

    monkeypatch.setattr(oauth_helpers, "mwoauth", FailingMWOAuth())
    with pytest.raises(oauth_helpers.OAuthIdentityError):
        oauth_helpers.complete_login(("rk", "rs"), "x=1")
