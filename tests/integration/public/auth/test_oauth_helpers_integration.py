"""Integration tests for OAuth helper functions."""

from mwoauth import RequestToken

from src.main_app import AppFactory
from src.main_app.config import TestingConfig
from src.main_app.services.auth import auth_service as oauth_helpers
from src.main_app.services.auth.auth_service import OAuthService


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
        return "https://example.org/redirect", RequestToken("req-key", "req-secret")

    def complete(self, _request_token, _query_string):
        return RequestToken("acc-key", "acc-secret")

    def identify(self, _access_token):
        return {"username": "Alice", "sub": 123}


def test_start_login_returns_redirect_and_request_token(monkeypatch):
    monkeypatch.setattr(oauth_helpers, "ConsumerToken", StubConsumerToken)
    monkeypatch.setattr(oauth_helpers, "Handshaker", StubHandshaker)
    app = AppFactory.create(TestingConfig)
    with app.test_request_context("/"):
        redirect_url, request_token, request_srcret = OAuthService().create_authorization_url(
            "https://host/callback?state=signed-state"
        )
        assert redirect_url.startswith("https://example.org/redirect")
        assert request_token == "req-key"
        assert request_srcret == "req-secret"
