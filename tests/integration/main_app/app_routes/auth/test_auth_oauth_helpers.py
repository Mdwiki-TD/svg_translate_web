"""Integration tests for OAuth helper functions."""

from types import SimpleNamespace

from src.main_app import create_app
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
        # return as tuple to exercise tuple path in complete_login
        return ("acc-key", "acc-secret")

    def identify(self, _access_token):
        return {"username": "Alice", "sub": 123}


class StubMWOAuth(SimpleNamespace):
    def __init__(self):
        super().__init__(ConsumerToken=StubConsumerToken, Handshaker=StubHandshaker)


def test_start_login_returns_redirect_and_request_token(monkeypatch):
    monkeypatch.setattr(oauth_helpers, "mwoauth", StubMWOAuth())
    app = create_app()
    with app.test_request_context("/"):
        redirect_url, request_token = oauth_helpers.start_login("signed-state")
        assert redirect_url.startswith("https://example.org/redirect")
        assert isinstance(request_token, tuple) and len(request_token) == 2
