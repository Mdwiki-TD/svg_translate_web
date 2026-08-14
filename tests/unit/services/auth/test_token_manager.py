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

    def _seed_user(self, username: str) -> int:
        """Create a user identity row. Returns user_id.

        Mirrors how the route resolves identity (ensure_exists) before handing
        a user_id to TokenManager.save_token.
        """
        with self.app.app_context():
            user = UsersService().create_user(username)

            assert user is not None
            return user.user_id

    def _seed_admin(self, username: str) -> None:
        """Create an active coordinator record."""
        with self.app.app_context():
            AdminService().add_coordinator(username)

    # ── save_token ──

    def test_save_and_get_user_empty_username(self):
        assert self.service.save_token("", "key", "secret") is None

    def test_save_and_get_user_existing_user(self):
        """Existing user (already resolved to a user_id) gets its token upserted and admin status checked."""
        user_id = self._seed_user("testuser")
        self._seed_admin("testuser")

        with self.app.app_context():
            self.service.save_token(user_id, "new_key", "new_secret")
            res = self.service.get_authenticated_user(user_id)

        assert res is not None
        assert res.user_id == user_id
        assert res.username == "testuser"
        assert res.is_active_admin is True

    def test_save_and_get_user_new_user(self):
        """A user with no token yet should get one upserted and non-admin status returned.

        Mirrors the route flow: the user identity is resolved to a user_id upstream
        (via ensure_exists), then TokenManager.save_token persists the encrypted token.
        """
        user_id = self._seed_user("brand_new_user")

        with self.app.app_context():
            self.service.save_token(user_id, "k2", "s2")
            res = self.service.get_authenticated_user(user_id)

        assert res is not None
        assert res.user_id == user_id
        assert res.username == "brand_new_user"
        assert res.is_active_admin is False

        # Verify the token was persisted
        with self.app.app_context():
            token = UserTokenService().get_record_by_id(user_id)
            assert token is not None

    def test_save_and_get_user_upsert_fail(self, monkeypatch: pytest.MonkeyPatch):
        """When persisting the token raises, save_token should return None."""
        user_id = self._seed_user("user")

        def raise_error(*args, **kwargs):
            raise Exception("DB Error")

        monkeypatch.setattr(
            "src.main_app.services.auth.token_manager.UserTokenService.upsert_user_token",
            raise_error,
        )
        assert self.service.save_token(user_id, "k", "s") is None

    def test_save_and_get_record_by_id_fail(self, monkeypatch: pytest.MonkeyPatch):
        """When upsert succeeds but upsert_by raises, should return None."""
        user_id = self._seed_user("user")

        def raise_error(*args, **kwargs):
            raise Exception("Token Error")

        monkeypatch.setattr(
            "src.main_app.services.auth.token_manager.UserTokenService.upsert_by",
            raise_error,
        )
        self.service.save_token(user_id, "k", "s")
        assert self.service.get_authenticated_user(user_id) is None

    # ── get_authenticated_user ──

    def test_get_authenticated_user_success(self):
        """Seeded user + token + coordinator should return a valid CurrentUser."""
        user_id = self._seed_user("authuser")
        self._seed_admin("authuser")

        # TokenManager.save_token creates the token row (as the route would)
        with self.app.app_context():
            self.service.save_token(user_id, "k", "s")

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
