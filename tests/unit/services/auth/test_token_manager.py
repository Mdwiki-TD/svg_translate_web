"""
Unit tests for TokenManager.

Uses real DB services with the TestingConfig SQLite database.
Only monkeypatches specific methods to simulate error paths.
"""

from __future__ import annotations

import pytest
from flask import Flask

from src.main_app.database.services import AdminService, UsersService, UserTokenService
from src.main_app.services.auth.token_manager import TokenManager


@pytest.mark.usefixtures("mock_app")
class TestUserService:
    @pytest.fixture(autouse=True)
    def setup(self, mock_app: Flask):
        self.app = mock_app
        self.service = TokenManager()

    # ── helpers ──

    def _seed_user(self, username: str, *, access_key: str = "k", access_secret: str = "s") -> int:
        """Create a user + OAuth token record. Returns user_id."""
        with self.app.app_context():
            user = UsersService().create_user(username)

            assert user is not None

            UserTokenService().upsert_user_token(
                user_id=user.user_id,
                encrypted_token=b"access_key",
                encrypted_secret=b"access_secret",
            )
            return user.user_id

    def _seed_admin(self, username: str) -> None:
        """Create an active coordinator record."""
        with self.app.app_context():
            AdminService().add_coordinator(username)

    # ── save_token ──

    def test_save_and_get_user_empty_username(self):
        assert self.service.save_token("", "key", "secret") is None

    def test_save_and_get_user_existing_user(self):
        """Existing user should be found, token upserted, and admin status checked."""
        user_id = self._seed_user("testuser")
        self._seed_admin("testuser")

        with self.app.app_context():
            res = self.service.save_token("testuser", "new_key", "new_secret")

        assert res is not None
        assert res.user_id == user_id
        assert res.username == "testuser"
        assert res.is_active_admin is True

    def test_save_and_get_user_new_user(self):
        """New user should be created, token upserted, and non-admin status returned."""
        with self.app.app_context():
            res = self.service.save_token("brand_new_user", "k2", "s2")

        assert res is not None
        assert res.username == "brand_new_user"
        assert res.is_active_admin is False

        # Verify user was persisted
        with self.app.app_context():
            user = UsersService().get_user_by_username("brand_new_user")
            assert user is not None

    def test_save_and_get_user_upsert_fail(self, monkeypatch: pytest.MonkeyPatch):
        """When user lookup raises, save_token should return None."""

        def raise_error(*args, **kwargs):
            raise Exception("DB Error")

        monkeypatch.setattr(
            "src.main_app.services.auth.token_manager.UsersService.get_user_by_username",
            raise_error,
        )
        assert self.service.save_token("user", "k", "s") is None

    def test_save_and_get_record_by_id_fail(self, monkeypatch: pytest.MonkeyPatch):
        """When upsert succeeds but get_record_by_id raises, should return None."""
        self._seed_user("user")

        def raise_error(*args, **kwargs):
            raise Exception("Token Error")

        monkeypatch.setattr(
            "src.main_app.services.auth.token_manager.UserTokenService.get_record_by_id",
            raise_error,
        )
        assert self.service.save_token("user", "k", "s") is None

    # ── get_authenticated_user ──

    def test_get_authenticated_user_success(self):
        """Seeded user + token + coordinator should return a valid CurrentUser."""
        user_id = self._seed_user("authuser")
        self._seed_admin("authuser")

        with self.app.app_context():
            res = self.service.get_authenticated_user(user_id)

        assert res is not None
        assert res.username == "authuser"
        assert res.is_active_admin is True

    def test_get_authenticated_user_not_found(self):
        """Non-existent user_id should return None (no token in DB)."""
        with self.app.app_context():
            assert self.service.get_authenticated_user(99999) is None

    def test_get_authenticated_user_error(self, monkeypatch: pytest.MonkeyPatch):
        """When get_authenticated_user_token raises, should return None."""

        def raise_error(*args, **kwargs):
            raise Exception("Load error")

        monkeypatch.setattr(
            "src.main_app.services.auth.token_manager.UserTokenService.get_authenticated_user_token",
            raise_error,
        )
        assert self.service.get_authenticated_user(123) is None
