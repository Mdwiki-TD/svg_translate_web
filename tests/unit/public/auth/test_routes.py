"""Unit tests for src/main_app/public/auth/routes.py."""

from __future__ import annotations

from unittest.mock import Mock


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
