"""Tests for src.main_app.api_services.clients.commons_client."""

from __future__ import annotations

import requests

from src.main_app.api_services.clients.commons_client import (
    create_commons_session,
)


class TestCreateCommonsSession:
    """Tests for create_commons_session function."""

    def test_creates_session(self):
        """Test that a requests Session is created."""
        session = create_commons_session()
        assert isinstance(session, requests.Session)

    def test_default_user_agent(self):
        """Test default User-Agent header."""
        session = create_commons_session()
        assert session.headers["User-Agent"] == "SVGTranslateBot/1.0"

    def test_custom_user_agent(self):
        """Test custom User-Agent header."""
        session = create_commons_session("MyBot/2.0")
        assert session.headers["User-Agent"] == "MyBot/2.0"
