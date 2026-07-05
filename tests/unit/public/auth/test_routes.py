"""Unit tests for src/main_app/public/auth/routes.py."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

import pytest


@pytest.mark.usefixtures("mock_app")
class TestAuthRoutes:
    def test_login_redirects(self, mock_client):
        resp = mock_client.get("/login")
        assert resp.status_code == 302

    def test_logout_redirects(self, mock_client):
        resp = mock_client.get("/logout")
        assert resp.status_code == 302


class TestClientKey:
    def test_uses_forwarded_for(self, monkeypatch):
        mock_req = Mock()
        mock_req.headers.get.return_value = "1.2.3.4, 5.6.7.8"
        mock_req.remote_addr = "9.10.11.12"
        monkeypatch.setattr("src.main_app.public.auth.routes.request", mock_req)
        from src.main_app.public.auth.routes import _client_key

        assert _client_key() == "1.2.3.4"

    def test_falls_back_to_remote_addr(self, monkeypatch):
        mock_req = Mock()
        mock_req.headers.get.return_value = None
        mock_req.remote_addr = "1.2.3.4"
        monkeypatch.setattr("src.main_app.public.auth.routes.request", mock_req)
        from src.main_app.public.auth.routes import _client_key

        assert _client_key() == "1.2.3.4"

    def test_falls_back_to_anonymous(self, monkeypatch):
        mock_req = Mock()
        mock_req.headers.get.return_value = None
        mock_req.remote_addr = None
        monkeypatch.setattr("src.main_app.public.auth.routes.request", mock_req)
        from src.main_app.public.auth.routes import _client_key

        assert _client_key() == "anonymous"


class TestLoadRequestToken:
    def test_valid_token(self, monkeypatch):
        monkeypatch.setattr("src.main_app.public.auth.routes.RequestToken", lambda k, s: f"token:{k}:{s}")
        from src.main_app.public.auth.routes import _load_request_token

        result = _load_request_token(["key", "secret"])
        assert result is not None

    def test_none_raises(self, monkeypatch):
        from src.main_app.public.auth.routes import _load_request_token

        with pytest.raises(ValueError, match="Missing OAuth request token"):
            _load_request_token(None)

    def test_short_raises(self, monkeypatch):
        from src.main_app.public.auth.routes import _load_request_token

        with pytest.raises(ValueError, match="Invalid OAuth request token"):
            _load_request_token(["only"])


class TestSetResponseCookies:
    def test_sets_cookie(self, monkeypatch):
        from src.main_app.public.auth.routes import _set_response_cookies

        mock_response = Mock()
        mock_settings = MagicMock()
        mock_settings.cookie.name = "auth_cookie"
        mock_settings.cookie.httponly = True
        mock_settings.cookie.secure = False
        mock_settings.cookie.samesite = "Lax"
        mock_settings.cookie.max_age = 3600
        monkeypatch.setattr("src.main_app.public.auth.routes.settings", mock_settings)
        mock_sign = Mock(return_value="signed_user_id")
        monkeypatch.setattr("src.main_app.public.auth.routes.sign_user_id", mock_sign)
        _set_response_cookies(123, mock_response)
        mock_response.set_cookie.assert_called_once_with(
            "auth_cookie",
            "signed_user_id",
            httponly=True,
            secure=False,
            samesite="Lax",
            max_age=3600,
            path="/",
        )


class TestLogout:
    def test_logout_clears_session(self, mock_client, monkeypatch):
        with mock_client.session_transaction() as session:
            session["uid"] = 123
            session["username"] = "testuser"
        resp = mock_client.get("/logout")
        assert resp.status_code == 302
        with mock_client.session_transaction() as session:
            assert "uid" not in session
            assert "username" not in session

    def test_logout_no_uid(self, mock_client, monkeypatch):
        resp = mock_client.get("/logout")
        assert resp.status_code == 302
