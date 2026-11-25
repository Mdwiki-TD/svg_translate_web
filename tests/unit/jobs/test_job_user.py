"""Tests for ``jobs.job_user``."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from src.main_app.jobs.job_user import SYSTEM_USERNAME, build_job_user, system_user


@pytest.fixture
def mock_user_token_service_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = MagicMock()
    _mock_class.return_value = MagicMock()
    monkeypatch.setattr(
        "src.main_app.database.services.users.user_token_service.UserTokenService",
        _mock_class,
    )
    return _mock_class


@pytest.fixture
def mock_token_manager_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = MagicMock()
    _mock_class.return_value = MagicMock()
    monkeypatch.setattr(
        "src.main_app.services.auth.token_manager.TokenManager",
        _mock_class,
    )
    return _mock_class


class TestSystemUser:
    def test_username_is_the_background_job_identity(self) -> None:
        assert SYSTEM_USERNAME == "Background job"
        assert system_user() == {"username": "Background job"}

    def test_returns_a_fresh_dict_each_call(self) -> None:
        first = system_user()
        first["access_token"] = "leaked"

        assert system_user() == {"username": SYSTEM_USERNAME}


class TestBuildJobUser:
    def test_returns_none_when_user_has_no_token(
        self,
        mock_user_token_service_class: MagicMock,
        mock_token_manager_class: MagicMock,
    ) -> None:
        mock_user_token_service_class.return_value.get_user_token_by_username.return_value = None

        assert build_job_user("alice") is None
        mock_token_manager_class.return_value.get_authenticated_user.assert_not_called()

    def test_returns_none_when_user_cannot_be_authenticated(
        self,
        mock_user_token_service_class: MagicMock,
        mock_token_manager_class: MagicMock,
    ) -> None:
        mock_user_token_service_class.return_value.get_user_token_by_username.return_value = MagicMock(user_id=3)
        mock_token_manager_class.return_value.get_authenticated_user.return_value = None

        assert build_job_user("alice") is None

    def test_returns_auth_payload(
        self,
        mock_user_token_service_class: MagicMock,
        mock_token_manager_class: MagicMock,
    ) -> None:
        mock_user_token_service_class.return_value.get_user_token_by_username.return_value = MagicMock(user_id=3)
        user = MagicMock()
        user.to_auth_payload.return_value = {"id": 3, "username": "alice"}
        mock_token_manager_class.return_value.get_authenticated_user.return_value = user

        assert build_job_user("alice") == {"id": 3, "username": "alice"}
        mock_user_token_service_class.return_value.get_user_token_by_username.assert_called_once_with("alice")
        mock_token_manager_class.return_value.get_authenticated_user.assert_called_once_with(3)
