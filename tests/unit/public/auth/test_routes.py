"""Unit tests for src/main_app/public/auth/routes.py."""

from __future__ import annotations

from unittest.mock import Mock

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
