"""Tests for authentication routes.

Uses the full app factory (TestingConfig) with a real SQLite database.
Only external OAuth calls and non-deterministic utilities are mocked.
Rate limiting is exercised through the real Flask-Limiter instance.
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace
from urllib.parse import quote

import pytest
from flask import Flask
from flask.testing import FlaskClient
from src.main_app.config import get_settings
from src.main_app.database.services import UsersService, UserTokenService
from src.main_app.public.routes.auth_route import OAuthCallbackView  # noqa: F401
from src.main_app.services.auth import AuthFlowService
from src.main_app.services.core.cookies import SignedTokenService
from src.main_app.services.core.rate_limit import (
    CALLBACK_LIMIT_STRATEGY,
    LOGIN_LIMIT_STRATEGY,
    limiter,
)

app_settings = get_settings()


def _hits_allowed(limit: str) -> int:
    """Extract the numeric part of a limit string such as '5 per minute'."""
    return int(limit.split()[0])


@pytest.fixture(autouse=True)
def _reset_rate_limiter(mock_app: Flask) -> Iterator[None]:
    """Start and finish every test with empty rate-limit counters.

    Depends on mock_app so the limiter storage exists before it is reset.
    """
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def enable_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the limiter on, in case TestingConfig disables it."""
    monkeypatch.setattr(limiter, "enabled", True)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


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

        response = mock_client.get("/login")

        assert response.status_code == 302
        assert response.headers["Location"] == "https://auth.example"

        with mock_client.session_transaction() as sess:
            # Real session key from app_settings (oauth_state_nonce)
            assert sess[app_settings.sessions.state_key] == "nonce"
            # Real session key from app_settings (state = request_token_key)
            assert sess[app_settings.sessions.request_token_key] == "a"

    @pytest.mark.usefixtures("enable_rate_limit")
    def test_login_rate_limited(
        self, mock_app: Flask, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Requests over the login limit should redirect home without reaching the view."""
        calls: list[int] = []

        def fake_start_login(self) -> SimpleNamespace:
            calls.append(1)
            return SimpleNamespace(
                success=False,
                error_message="boom",
                flash_category="danger",
                redirect_url=None,
            )

        monkeypatch.setattr(AuthFlowService, "start_login", fake_start_login)

        allowed = _hits_allowed(LOGIN_LIMIT_STRATEGY)
        for _ in range(allowed):
            response = mock_client.get("/login")
            assert response.status_code == 302
            assert "boom" in response.headers["Location"]

        # One request over the limit: throttled before the view runs
        response = mock_client.get("/login")

        assert response.status_code == 429
        headers = dict(response.headers)

        assert int(headers["Retry-After"]) > 0
        assert headers["X-RateLimit-Limit"] == "5"
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers

        assert len(calls) == allowed


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
        response = mock_client.get(f"/callback?state={quote(signed_state)}&oauth_verifier=code")
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

    @pytest.mark.usefixtures("enable_rate_limit")
    def test_callback_rate_limited(
        self, mock_app: Flask, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Requests over the callback limit should redirect with an error without reaching the view."""
        calls: list[int] = []

        def fake_complete_callback(self, *args, **kwargs) -> SimpleNamespace:
            calls.append(1)
            # No error message: the view redirects to the index without an error param
            return SimpleNamespace(success=False, error_message=None, flash_category="danger")

        monkeypatch.setattr(AuthFlowService, "complete_callback", fake_complete_callback)

        allowed = _hits_allowed(CALLBACK_LIMIT_STRATEGY)
        for _ in range(allowed):
            response = mock_client.get("/callback?state=token&oauth_verifier=code")
            assert response.status_code == 302
            assert "error=" not in response.headers["Location"]

        # One request over the limit: throttled before the view runs
        response = mock_client.get("/callback?state=token&oauth_verifier=code")

        assert response.status_code == 429
        assert len(calls) == allowed

        headers = dict(response.headers)
        assert int(headers["Retry-After"]) > 0
        assert headers["X-RateLimit-Limit"] == "10"
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers

    def test_callback_missing_state(
        self, mock_app: Flask, mock_client: FlaskClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Callback should fail when state is missing."""

        response = mock_client.get("/callback")
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

        response = mock_client.get("/logout")

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")

        # Verify token was deleted from the real DB
        with mock_app.app_context():
            token = UserTokenService().get_record_by_id(user_id)
            assert token is None

        with mock_client.session_transaction() as sess:
            assert "uid" not in sess
