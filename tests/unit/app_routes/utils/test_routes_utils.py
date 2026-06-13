# ruff: noqa: F401
"""
Unit tests for src/main_app/app_routes/utils/routes_utils.py module.

Functions to test: context_user, load_auth_payload, get_job_detail_url

TODO: write tests
"""

from __future__ import annotations

from unittest.mock import MagicMock

from src.main_app.app_routes.utils.routes_utils import (
    can_run_bg_jobs,
    can_run_jobs,
    context_user,
    get_job_detail_url,
    load_auth_payload,
)
from src.main_app.su_services.current_user import CurrentUser


class TestLoadAuthPayload:
    def test_with_current_user(self):
        user = CurrentUser(user_id=42, username="TestUser", access_token=b"token123", access_secret=b"secret456")
        result = load_auth_payload(user)
        assert result["id"] == 42
        assert result["username"] == "TestUser"
        assert result["access_token"] == b"token123"
        assert result["access_secret"] == b"secret456"

    def test_with_none(self):
        result = load_auth_payload(None)
        assert result == {}

    def test_returns_dict(self):
        result = load_auth_payload(None)
        assert isinstance(result, dict)

    def test_with_current_user_returns_dict(self):
        user = CurrentUser(user_id=1, username="u", access_token=b"t", access_secret=b"s")
        result = load_auth_payload(user)
        assert isinstance(result, dict)
        assert len(result) == 4

    def test_with_magic_mock_fallback(self):
        """MagicMock without to_auth_payload should use fallback path."""
        user = MagicMock(spec=["user_id", "username", "access_token", "access_secret"])
        user.user_id = 42
        user.username = "TestUser"
        user.access_token = "token123"
        user.access_secret = "secret456"
        result = load_auth_payload(user)
        assert result["id"] == 42
        assert result["username"] == "TestUser"
