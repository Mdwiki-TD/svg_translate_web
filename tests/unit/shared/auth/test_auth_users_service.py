"""Unit tests for AuthUserService."""

from __future__ import annotations

import pytest

from src.main_app.db.services import AdminService, UsersService, UserTokenService
from src.main_app.shared.auth.auth_users_service import AuthUserService


@pytest.fixture
def service() -> AuthUserService:
    return AuthUserService()


class TestSaveAndGetUser:
    def test_empty_username(self, service: AuthUserService) -> None:
        assert service.save_and_get_user("", "key", "secret") is None

    def test_existing_user(self, service: AuthUserService) -> None:
        UsersService().create_user("testuser")

        res = service.save_and_get_user("testuser", "access_key", "access_secret")

        assert res is not None
        assert res.username == "testuser"
        assert res.is_active_admin is False

    def test_new_user(self, service: AuthUserService) -> None:
        res = service.save_and_get_user("newuser", "new_key", "new_secret")

        assert res is not None
        assert res.username == "newuser"
        assert res.is_active_admin is False
        record = UserTokenService().get_authenticated_user_token(res.user_id)
        assert record is not None

    def test_existing_user_is_active_admin(self, service: AuthUserService) -> None:
        UsersService().create_user("adminuser")
        AdminService().add_coordinator("adminuser")

        res = service.save_and_get_user("adminuser", "k", "s")

        assert res is not None
        assert res.username == "adminuser"
        assert res.is_active_admin is True


class TestGetAuthenticatedUser:
    def test_success(self, service: AuthUserService) -> None:
        user = UsersService().create_user("authuser")
        UserTokenService().upsert_user_token(user.user_id, "atk", "as")

        res = service.get_authenticated_user(user.user_id)

        assert res is not None
        assert res.username == "authuser"
        assert res.is_active_admin is False

    def test_not_found(self, service: AuthUserService) -> None:
        res = service.get_authenticated_user(999)

        assert res is None
