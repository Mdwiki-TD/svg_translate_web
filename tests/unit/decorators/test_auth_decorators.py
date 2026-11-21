"""Tests for authentication utilities and decorators."""

from __future__ import annotations

import pytest
from flask import Flask, g, session
from src.main_app.decorators.auth_decorators import oauth_required


class TestOAuthRequired:
    """Tests for oauth_required decorator."""

    def test_redirects_when_no_user_and_oauth_enabled(
        self,
        mock_app,
        mock_get_current_user,
    ):
        """Test that decorator redirects when no user and OAuth enabled."""
        mock_get_current_user.return_value = None

        @oauth_required
        def protected_view():
            return "success"

        with mock_app.test_request_context():
            from flask import session

            session["uid"] = None

            result = protected_view()

            assert result.status_code == 302  # type: ignore # Redirect

    def test_allows_access_when_user_present(self, mock_app, mock_get_current_user):
        """Test that decorator allows access when user is present."""

        @oauth_required
        def protected_view():
            return "success"

        with mock_app.test_request_context():
            result = protected_view()
            # AssertionError: assert <<class 'pytest_flask.plugin.JSONResponse'> 209 bytes [302 FOUND]> == 'success'
            assert result == "success"

    def test_decorator_calls_function_when_user_exists(self, mock_app: Flask) -> None:
        with mock_app.test_request_context():
            g._current_user = "alice"

            @oauth_required
            def dummy():
                return "ok"

            assert dummy() == "ok"

    def test_redirects_to_login_when_user_is_none(self, mock_app: Flask) -> None:
        with mock_app.test_request_context():
            with mock_app.test_client() as client:
                with client.session_transaction() as sess:
                    sess.clear()

            @oauth_required
            def dummy():
                return "never reached"

            resp = dummy()
            assert resp.status_code == 302  # type: ignore
            assert resp.location in ("/login", "/auth/login")  # type: ignore

    def test_sets_post_login_redirect_in_session(self, mock_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        with mock_app.test_request_context(
            base_url="https://example.com/",
            path="/some/protected/page",
        ):
            with mock_app.test_client() as client:
                with client.session_transaction() as sess:
                    sess.clear()

            @oauth_required
            def dummy():
                return "never reached"

            dummy()
            assert session["post_login_redirect"] == "https://example.com/some/protected/page"
