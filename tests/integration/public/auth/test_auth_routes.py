"""Tests for authentication routes."""

from __future__ import annotations

import types

import pytest
from flask import Blueprint, Flask

from src.main_app.public.auth.routes import AuthRoutes


@pytest.fixture
def auth_app(monkeypatch: pytest.MonkeyPatch) -> Flask:
    app = Flask(__name__)
    app.secret_key = "test-secret"
    app.config["SERVER_NAME"] = "example.com"

    cookie = types.SimpleNamespace(
        name="uid_enc_copy",
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
    monkeypatch.setattr("src.main_app.public.auth.routes.settings", settings)
    monkeypatch.setattr("src.main_app.public.auth.routes.oauth_state_nonce", "state")
    monkeypatch.setattr("src.main_app.public.auth.routes.request_token_key", "req_token")
    monkeypatch.setattr("src.main_app.public.auth.routes.load_logged_in_user", lambda: None)

    bp = Blueprint("auth", __name__)
    AuthRoutes(bp)
    app.register_blueprint(bp)
    app.add_url_rule("/", "main.index", lambda: "index")

    return app


def test_login_success_flow(auth_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyLimiter:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def allow(self, key: str) -> bool:
            self.calls.append(key)
            return True

        def try_after(self, key: str):  # pragma: no cover - defensive guard
            raise AssertionError("try_after should not be called")

    limiter = DummyLimiter()
    monkeypatch.setattr("src.main_app.public.auth.routes.login_rate_limiter", limiter)
    monkeypatch.setattr(
        "src.main_app.public.auth.routes.secrets",
        types.SimpleNamespace(**{"token_urlsafe": lambda _: "nonce"}),
    )
    monkeypatch.setattr("src.main_app.public.auth.routes.sign_state_token", lambda state: f"signed:{state}")

    class DummyStart:
        def __call__(self, token: str):
            assert token == "signed:nonce"
            return "https://auth.example", ("a", "b")

    monkeypatch.setattr("src.main_app.public.auth.routes.start_login", DummyStart())

    client = auth_app.test_client()
    response = client.get("/login")

    assert response.status_code == 302
    assert response.headers["Location"] == "https://auth.example"

    with client.session_transaction() as sess:
        assert sess["state"] == "nonce"
        assert sess["req_token"] == ["a", "b"]

    assert limiter.calls


def test_callback_success(auth_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    class DummyLimiter:
        def allow(self, key: str) -> bool:
            return True

    monkeypatch.setattr("src.main_app.public.auth.routes.callback_rate_limiter", DummyLimiter())
    monkeypatch.setattr(
        "src.main_app.public.auth.routes.verify_state_token",
        lambda token: "state-value" if token == "token" else None,
    )
    monkeypatch.setattr("src.main_app.public.auth.routes._load_request_token", lambda raw: ("k", "s"))

    def fake_complete(request_token, query_string: str):
        assert request_token == ("k", "s")
        assert query_string == "state=token&oauth_verifier=code"
        access = types.SimpleNamespace(key="ak", secret="as")
        identity = {"sub": "123", "username": "Tester"}
        return access, identity

    monkeypatch.setattr("src.main_app.shared.auth.auth_service.complete_login", fake_complete)

    fake_user = types.SimpleNamespace(user_id=123, username="Tester")
    monkeypatch.setattr(
        "src.main_app.shared.auth.auth_users_service.AuthUserService.save_and_get_user",
        staticmethod(lambda **kwargs: fake_user),
    )
    monkeypatch.setattr("src.main_app.public.auth.routes.sign_user_id", lambda user_id: f"signed:{user_id}")

    client = auth_app.test_client()
    with client.session_transaction() as sess:
        sess["state"] = "state-value"
        sess["req_token"] = ["k", "s"]

    response = client.get("/callback?state=token&oauth_verifier=code")
    cookie_header = response.headers.get("Set-Cookie", "")

    assert response.status_code == 302
    assert "uid_enc_copy" in cookie_header

    with client.session_transaction() as sess:
        assert sess["uid"] == 123


def test_logout_clears_session(auth_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.main_app.public.auth.routes.delete_user_token", lambda uid: None)
    monkeypatch.setattr("src.main_app.public.auth.routes.extract_user_id", lambda token: 55)

    client = auth_app.test_client()
    with client.session_transaction() as sess:
        sess["uid"] = 42
        sess["username"] = "Tester"

    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    with client.session_transaction() as sess:
        assert "uid" not in sess


def test_login_rate_limited(auth_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test login redirects when rate limited."""

    class DummyLimiter:
        def allow(self, key: str) -> bool:
            return False

        def try_after(self, key: str):
            return type("obj", (object,), {"total_seconds": lambda self: 60})()

    limiter = DummyLimiter()
    monkeypatch.setattr("src.main_app.public.auth.routes.login_rate_limiter", limiter)

    client = auth_app.test_client()
    response = client.get("/login")

    assert response.status_code == 302


def test_callback_rate_limited(auth_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test callback redirects when rate limited."""

    class DummyLimiter:
        def allow(self, key: str) -> bool:
            return False

    limiter = DummyLimiter()
    monkeypatch.setattr("src.main_app.public.auth.routes.callback_rate_limiter", limiter)

    client = auth_app.test_client()
    response = client.get("/callback?state=token&oauth_verifier=code")

    assert response.status_code == 302


def test_callback_missing_state(auth_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test callback fails when state is missing."""

    class DummyLimiter:
        def allow(self, key: str) -> bool:
            return True

    monkeypatch.setattr("src.main_app.public.auth.routes.callback_rate_limiter", DummyLimiter())

    client = auth_app.test_client()
    response = client.get("/callback")

    assert response.status_code == 302


def test_load_request_token_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _load_request_token parses valid token."""
    from mwoauth import RequestToken

    from src.main_app.public.auth.routes import _load_request_token

    result = _load_request_token(["key", "secret"])
    assert isinstance(result, RequestToken)
    assert result.key == "key"
    assert result.secret == "secret"


def test_load_request_token_invalid_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _load_request_token raises on empty token."""
    from src.main_app.public.auth.routes import _load_request_token

    with pytest.raises(ValueError, match="Missing OAuth request token"):
        _load_request_token(None)

    with pytest.raises(ValueError, match="Missing OAuth request token"):
        _load_request_token([])


def test_load_request_token_invalid_short(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test _load_request_token raises on short token."""
    from src.main_app.public.auth.routes import _load_request_token

    with pytest.raises(ValueError, match="Invalid OAuth request token"):
        _load_request_token(["key"])
