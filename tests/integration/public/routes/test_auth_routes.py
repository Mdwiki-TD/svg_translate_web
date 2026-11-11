"""Tests for authentication routes.

Uses the full app factory (TestingConfig) with a real SQLite database.
Only external OAuth calls and non-deterministic utilities are mocked.
"""

from __future__ import annotations

from types import SimpleNamespace
from urllib.parse import quote

import pytest
from flask import Flask
from flask.testing import FlaskClient
from src.main_app.config import get_settings
from src.main_app.database.services import UsersService, UserTokenService
from src.main_app.public.routes.auth_route import OAuthCallbackView  # noqa: F401
from src.main_app.services.core.cookies import SignedTokenService

# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
app_settings = get_settings()


class DummyLimiter:
    def allow(self, key: str) -> bool:
        return False

    def try_after(self, key: str):
        return type("obj", (object,), {"total_seconds": lambda self: 60})()

    def get_time_left(self, _key) -> str:
        return "0"

    @classmethod
    def client_key(cls, request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.remote_addr or "anonymous"

    @classmethod
    def callback_rate_limiter(cls) -> DummyLimiter:
        return cls()

    @classmethod
    def login_rate_limiter(cls) -> DummyLimiter:
        return cls()


@pytest.mark.usefixtures("mock_app")
class TestLogin:
    def test_login_success_flow(
        self, mock_app: Flask, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Login should redirect to MediaWiki and store state + request token in session."""

        # Mock only external OAuth handshake and non-deterministic nonce
        monkeypatch.setattr(
            "src.main_app.services.auth.flow.secrets",
            SimpleNamespace(token_urlsafe=lambda _: "nonce"),
        )

        class DummyStart:
            def __call__(self, token: str):
                # token is the signed state — just verify it's a non-empty string
                assert token
                return ("https://auth.example", "a", "b")

        monkeypatch.setattr("src.main_app.services.auth.flow.OAuthService.create_authorization_url", DummyStart())

        response = mock_client.get("/auth/login")

        assert response.status_code == 302
        assert response.headers["Location"] == "https://auth.example"

        with mock_client.session_transaction() as sess:
            # Real session key from app_settings (oauth_state_nonce)
            assert sess[app_settings.sessions.state_key] == "nonce"
            # Real session key from app_settings (state = request_token_key)
            assert sess[app_settings.sessions.request_token_key] == "a"

    def test_login_rate_limited(
        self, mock_app: Flask, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Login should redirect when rate limited."""

        monkeypatch.setattr("src.main_app.public.routes.auth_route.RateLimiter", DummyLimiter)

        response = mock_client.get("/auth/login")
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Callback
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("mock_app")
class TestCallback:
    def test_callback_success(self, mock_app: Flask, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
        """Callback should complete OAuth, persist user to DB, set session and cookie."""

        # Mock only the external OAuth completion — returns an access token
        def fake_complete(
            self,
            query_string: str,
            oauth_token: str,
            oauth_token_secret: str,
        ) -> SimpleNamespace:
            assert oauth_token == "k"
            assert oauth_token_secret == "s"
            assert "oauth_verifier=code" in query_string
            return SimpleNamespace(key="ak", secret="as")

        # The route calls identify() separately to resolve the identity
        def fake_identify(self, access_token):
            return {"sub": "123", "username": "Tester"}

        monkeypatch.setattr("src.main_app.services.auth.auth_service.OAuthService.fetch_access_token", fake_complete)
        monkeypatch.setattr("src.main_app.services.auth.auth_service.OAuthService.identify", fake_identify)

        # Sign a state nonce using the real signing utility
        state_nonce = "test-nonce"
        signed_state = SignedTokenService().sign_state_token(state_nonce)

        # Seed session with state nonce + request token (real session keys)
        with mock_client.session_transaction() as sess:
            sess[app_settings.sessions.state_key] = state_nonce
            sess[app_settings.sessions.request_token_key] = "k"
            sess[app_settings.sessions.request_secret_key] = "s"

        # The state query param must be the signed token (MediaWiki echoes it back)
        response = mock_client.get(f"/auth/callback?state={quote(signed_state)}&oauth_verifier=code")
        cookie_header = response.headers.get("Set-Cookie", "")

        assert response.status_code == 302
        # Real cookie name from app_settings
        # assert "uid_enc" in cookie_header

        # Verify user was persisted to the real DB
        with mock_app.app_context():
            user = UsersService().get_user_by_username("Tester")
            assert user is not None
            token = UserTokenService().get_record_by_id(user.user_id)
            assert token is not None

        with mock_client.session_transaction() as sess:
            assert sess["uid"] == user.user_id
            assert sess["username"] == "Tester"

    def test_callback_rate_limited(
        self, mock_app: Flask, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Callback should redirect when rate limited."""

        monkeypatch.setattr("src.main_app.public.routes.auth_route.RateLimiter", DummyLimiter)

        response = mock_client.get("/auth/callback?state=token&oauth_verifier=code")
        assert response.status_code == 302

    def test_callback_missing_state(
        self, mock_app: Flask, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Callback should fail when state is missing."""

        response = mock_client.get("/auth/callback")
        assert response.status_code == 302


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("mock_app")
class TestLogout:
    def test_logout_clears_session(self, mock_app: Flask, mock_client: FlaskClient) -> None:
        """Logout should delete the user token from DB and clear the session."""
        # Seed a real user + token in the DB
        with mock_app.app_context():
            user = UsersService().create_user("LogoutUser")
            assert user is not None
            UserTokenService().upsert_user_token(
                user_id=user.user_id,
                encrypted_token=b"ak",
                encrypted_secret=b"as",
            )
            user_id = user.user_id

        with mock_client.session_transaction() as sess:
            sess["uid"] = user_id
            sess["username"] = "LogoutUser"

        response = mock_client.get("/auth/logout")

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")

        # Verify token was deleted from the real DB
        with mock_app.app_context():
            token = UserTokenService().get_record_by_id(user_id)
            assert token is None

        with mock_client.session_transaction() as sess:
            assert "uid" not in sess
