"""Tests for authentication utilities and decorators."""

from __future__ import annotations

import pytest
from flask import Flask, g, session

from src.main_app.public.auth.decorators import oauth_required


class TestOauthRequired:
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
            assert resp.location == "/login"  # type: ignore

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
