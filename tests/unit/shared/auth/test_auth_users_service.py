"""Unit tests for AuthUserService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.shared.auth.auth_users_service import AuthUserService


@pytest.fixture
def mock_db_services():
    with (
        patch("src.main_app.shared.auth.auth_users_service.get_user_by_username") as m_get_by_name,
        patch("src.main_app.shared.auth.auth_users_service.upsert_user_token") as m_update,
        patch("src.main_app.shared.auth.auth_users_service.create_user") as m_create,
        patch("src.main_app.shared.auth.auth_users_service.get_user_token") as m_get_token,
        patch("src.main_app.shared.auth.auth_users_service.is_active_coordinator") as m_is_coord,
        patch("src.main_app.shared.auth.auth_users_service.get_authenticated_user_token") as m_get_auth,
    ):
        yield {
            "get_by_name": m_get_by_name,
            "update": m_update,
            "create": m_create,
            "get_token": m_get_token,
            "is_coord": m_is_coord,
            "get_auth": m_get_auth,
        }


class TestUserService:
    def test_save_and_get_user_empty_username(self):
        assert AuthUserService.save_and_get_user("", "key", "secret") is None

    def test_save_and_get_user_existing_user(self, mock_db_services):
        user_mock = MagicMock(user_id=1)
        mock_db_services["get_by_name"].return_value = user_mock
        mock_db_services["get_token"].return_value = MagicMock(access_token="key", access_secret="secret")
        mock_db_services["is_coord"].return_value = True

        res = AuthUserService.save_and_get_user("testuser", "key", "secret")

        assert res.username == "testuser"
        assert res.is_active_admin is True
        mock_db_services["update"].assert_called_once_with(user_id=1, access_key="key", access_secret="secret")

    def test_save_and_get_user_new_user(self, mock_db_services):
        mock_db_services["get_by_name"].return_value = None
        mock_db_services["create"].return_value = MagicMock(user_id=2)
        mock_db_services["get_token"].return_value = MagicMock(access_token="k2", access_secret="s2")
        mock_db_services["is_coord"].return_value = False

        res = AuthUserService.save_and_get_user("newuser", "k2", "s2")

        assert res.user_id == 2
        assert res.is_active_admin is False
        mock_db_services["create"].assert_called_once()

    def test_save_and_get_user_upsert_fail(self, mock_db_services):
        mock_db_services["get_by_name"].side_effect = Exception("DB Error")
        assert AuthUserService.save_and_get_user("user", "k", "s") is None

    def test_save_and_get_user_token_fail(self, mock_db_services):
        mock_db_services["get_by_name"].return_value = MagicMock(user_id=1)
        mock_db_services["get_token"].side_effect = Exception("Token Error")
        assert AuthUserService.save_and_get_user("user", "k", "s") is None

    def test_get_authenticated_user_success(self, mock_db_services):
        mock_db_services["get_auth"].return_value = MagicMock(
            user=MagicMock(username="authuser"),
            access_token="atk",
            access_secret="as",
        )
        mock_db_services["is_coord"].return_value = True

        res = AuthUserService.get_authenticated_user(123)
        assert res.username == "authuser"
        assert res.is_active_admin is True

    def test_get_authenticated_user_not_found(self, mock_db_services):
        mock_db_services["get_auth"].return_value = None
        assert AuthUserService.get_authenticated_user(123) is None

    def test_get_authenticated_user_error(self, mock_db_services):
        mock_db_services["get_auth"].side_effect = Exception("Load error")
        assert AuthUserService.get_authenticated_user(123) is None
