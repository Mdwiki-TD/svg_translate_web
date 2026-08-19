from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask, g, session

from src.main_app.public.auth.decorators import (
    AUTOPATROL_REQUEST_URL,
    autopatrol_required,
    oauth_required,
)


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

    def test_sets_post_login_redirect_in_session(self, mock_app: Flask) -> None:
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


class TestAutopatrolRequired:
    def _user(self) -> MagicMock:
        user = MagicMock()
        user.to_auth_payload.return_value = {
            "id": 1,
            "username": "Alice",
            "access_token": b"token",
            "access_secret": b"secret",
        }
        return user

    def test_calls_function_for_autopatrolled_user(self, mock_app: Flask) -> None:
        with mock_app.test_request_context():
            user = self._user()
            g._current_user = user

            @autopatrol_required
            def dummy():
                return "ok"

            with patch(
                "src.main_app.public.auth.decorators.get_user_groups",
                return_value=frozenset({"user", "autopatrolled"}),
            ) as get_groups:
                assert dummy() == "ok"

            get_groups.assert_called_once_with(user.to_auth_payload())

    def test_accepts_autopatrol_group_alias(self, mock_app: Flask) -> None:
        with mock_app.test_request_context():
            g._current_user = self._user()

            @autopatrol_required
            def dummy():
                return "ok"

            with patch(
                "src.main_app.public.auth.decorators.get_user_groups",
                return_value=frozenset({"autopatrol"}),
            ):
                assert dummy() == "ok"

    def test_redirects_anonymous_user_to_login(self, mock_app: Flask) -> None:
        with mock_app.test_request_context(path="/public-jobs/copy/start"):
            g._current_user = None

            @autopatrol_required
            def dummy():
                return "never reached"

            response = dummy()

            assert response.status_code == 302
            assert response.location == "/login"
            assert session["post_login_redirect"].endswith("/public-jobs/copy/start")

    def test_shows_request_link_when_permission_is_missing(self, mock_app: Flask) -> None:
        with mock_app.test_request_context(path="/public-jobs/copy/start", method="POST"):
            g._current_user = self._user()

            @autopatrol_required
            def dummy():
                pytest.fail("A user without Autopatrol must not run the tool")

            with patch(
                "src.main_app.public.auth.decorators.get_user_groups",
                return_value=frozenset({"user", "autoconfirmed"}),
            ):
                response, status = dummy()

            assert status == 403
            body = response
            assert "Autopatrol permission required" in body
            assert AUTOPATROL_REQUEST_URL in body
            assert "Request Autopatrol permission" in body

    def test_denies_access_when_permission_cannot_be_verified(self, mock_app: Flask) -> None:
        with mock_app.test_request_context(path="/public-jobs/copy/start", method="POST"):
            g._current_user = self._user()

            @autopatrol_required
            def dummy():
                pytest.fail("The tool must not run when the permission check fails")

            with patch(
                "src.main_app.public.auth.decorators.get_user_groups", return_value=None
            ):
                response, status = dummy()

            assert status == 503
            assert "Permission check unavailable" in response
