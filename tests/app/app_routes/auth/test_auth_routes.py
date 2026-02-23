"""Tests for authentication routes."""

from __future__ import annotations

import types

import pytest
from flask import Flask, g, session

from src.main_app.app_routes.auth import routes


@pytest.fixture
def app(monkeypatch: pytest.MonkeyPatch) -> Flask:
    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.config["SERVER_NAME"] = "example.com"
    app.add_url_rule("/", "main.index", lambda: "index")
    app.add_url_rule("/callback", "auth.callback", lambda: "callback")

    cookie = types.SimpleNamespace(
        name="uid_enc",
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=3600,
    )
    oauth_cfg = types.SimpleNamespace(consumer_key="key", consumer_secret="secret")
    settings = types.SimpleNamespace(
        STATE_SESSION_KEY="state",
        REQUEST_TOKEN_SESSION_KEY="req_token",
        cookie=cookie,
        oauth=oauth_cfg,
    )
    monkeypatch.setattr("src.main_app.app_routes.auth.routes.settings", settings)
    monkeypatch.setattr("src.main_app.app_routes.auth.routes.oauth_state_nonce", "state")
    monkeypatch.setattr("src.main_app.app_routes.auth.routes.request_token_key", "req_token")

    return app


def test_login_required_redirects_when_anonymous(app: Flask) -> None:
    @routes.login_required
    def protected() -> str:
        return "protected"

    with app.test_request_context("/protected"):
        g.is_authenticated = False
        response = protected()

    assert response.status_code == 302
    assert response.headers["Location"].endswith("error=login-required")


def test_login_success_flow(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyLimiter:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def allow(self, key: str) -> bool:
            self.calls.append(key)
            return True

        def try_after(self, key: str):  # pragma: no cover - defensive guard
            raise AssertionError("try_after should not be called")

    limiter = DummyLimiter()
    monkeypatch.setattr("src.main_app.app_routes.auth.routes.login_rate_limiter", limiter)
    monkeypatch.setattr(routes.secrets, "token_urlsafe", lambda _: "nonce")
    monkeypatch.setattr("src.main_app.app_routes.auth.routes.sign_state_token", lambda state: f"signed:{state}")

    class DummyStart:
        def __call__(self, token: str):
            assert token == "signed:nonce"
            return "https://auth.example", ("a", "b")

    monkeypatch.setattr("src.main_app.app_routes.auth.routes.start_login", DummyStart())

    with app.test_request_context("/login"):
        response = routes.login()
        assert response.status_code == 302
        assert response.headers["Location"] == "https://auth.example"
        assert session["state"] == "nonce"
        assert session["req_token"] == ["a", "b"]

    assert limiter.calls


def test_callback_success(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyLimiter:
        def allow(self, key: str) -> bool:
            return True

    monkeypatch.setattr("src.main_app.app_routes.auth.routes.callback_rate_limiter", DummyLimiter())
    monkeypatch.setattr(
        "src.main_app.app_routes.auth.routes.verify_state_token",
        lambda token: "state-value" if token == "token" else None,
    )
    monkeypatch.setattr("src.main_app.app_routes.auth.routes._load_request_token", lambda raw: ("k", "s"))

    def fake_complete(request_token, query_string: str):
        assert request_token == ("k", "s")
        assert query_string == "state=token&oauth_verifier=code"
        access = types.SimpleNamespace(key="ak", secret="as")
        identity = {"sub": "123", "username": "Tester"}
        return access, identity

    monkeypatch.setattr("src.main_app.app_routes.auth.routes.complete_login", fake_complete)
    monkeypatch.setattr("src.main_app.app_routes.auth.routes.upsert_user_token", lambda **kwargs: kwargs)
    monkeypatch.setattr("src.main_app.app_routes.auth.routes.sign_user_id", lambda user_id: f"signed:{user_id}")

    with app.test_request_context("/callback?state=token&oauth_verifier=code"):
        session["state"] = "state-value"
        session["req_token"] = ["k", "s"]

        response = routes.callback()
        cookie_header = response.headers.get("Set-Cookie", "")

        assert response.status_code == 302
        assert "uid_enc" in cookie_header
        assert session["uid"] == 123
        assert g.current_user.username == "Tester"
        assert g.is_authenticated is True


def test_logout_clears_session(app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.main_app.app_routes.auth.routes.delete_user_token", lambda uid: None)
    monkeypatch.setattr("src.main_app.app_routes.auth.routes.extract_user_id", lambda token: 55)

    with app.test_request_context("/logout"):
        session["uid"] = 42
        session["username"] = "Tester"

        response = routes.logout()

        assert response.status_code == 302
        assert response.headers["Location"] == "/"
        assert "uid" not in session
        assert g.current_user is None
