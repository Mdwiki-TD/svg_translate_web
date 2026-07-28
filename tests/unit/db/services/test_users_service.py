"""Tests for users_service module."""

from __future__ import annotations

import pytest

from src.main_app.db.exceptions import UserNotFoundError
from src.main_app.db.services.users_service import UsersService


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = UsersService()


class TestListUsers(TestSetup):
    """Tests for list_users."""

    def test_returns_all_users(self) -> None:
        user_record = self.service.create_user("test_user")
        result = self.service.list_users()
        assert len(result) == 1
        assert result[0].user_id == user_record.user_id
        assert result[0].username == "test_user"

    def test_returns_empty_when_no_users(self) -> None:
        assert self.service.list_users() == []


class TestGetUser(TestSetup):
    """Tests for get_user."""

    def test_returns_user_by_valid_id(self) -> None:
        user_record = self.service.create_user("test_user")
        result = self.service.get_user(user_record.user_id)
        assert result is not None
        assert result.user_id == user_record.user_id
        assert result.username == "test_user"

    def test_returns_none_for_zero_id(self) -> None:
        assert self.service.get_user(0) is None

    def test_returns_none_for_none_id(self) -> None:
        assert self.service.get_user(None) is None  # type: ignore[arg-type]

    def test_returns_none_for_non_existent_id(self) -> None:
        assert self.service.get_user(999) is None


class TestGetUserByUsername(TestSetup):
    """Tests for get_user_by_username."""

    def test_returns_user_by_existing_username(self) -> None:
        user_record = self.service.create_user("test_user")
        result = self.service.get_user_by_username("test_user")
        assert result is not None
        assert result.user_id == user_record.user_id
        assert result.username == "test_user"

    def test_returns_none_for_empty_username(self) -> None:
        assert self.service.get_user_by_username("") is None
        assert self.service.get_user_by_username("  ") is None

    def test_returns_none_for_none_username(self) -> None:
        assert self.service.get_user_by_username(None) is None  # type: ignore[arg-type]

    def test_returns_none_for_non_existent_username(self) -> None:
        assert self.service.get_user_by_username("nonexistent") is None


class TestCreateUser(TestSetup):
    """Tests for create_user."""

    def test_creates_new_user(self) -> None:
        result = self.service.create_user("new_user")
        assert result.username == "new_user"
        assert result.user_id is not None

        persisted = self.service.get_by(username="new_user")
        assert persisted is not None
        assert persisted.user_id == result.user_id

    def test_returns_existing_user(self) -> None:
        user_record = self.service.create_user("test_user")
        result = self.service.create_user("test_user")
        assert result.user_id == user_record.user_id
        assert result.username == "test_user"


class TestToggleCanRunJobs(TestSetup):
    """Tests for toggle_can_run_jobs."""

    def test_toggles_to_true(self) -> None:
        user_record = self.service.create_user("test_user")
        result = self.service.toggle_can_run_jobs(user_record.user_id, True)
        assert bool(result.can_run_jobs) is True

        refreshed = self.service.get(user_record.user_id)
        assert refreshed is not None
        assert bool(refreshed.can_run_jobs) is True

    def test_toggles_to_false(self) -> None:
        user_record = self.service.create_user("test_user")
        result = self.service.toggle_can_run_jobs(user_record.user_id, False)
        assert bool(result.can_run_jobs) is False

        refreshed = self.service.get(user_record.user_id)
        assert refreshed is not None
        assert bool(refreshed.can_run_jobs) is False

    def test_raises_for_missing_user(self) -> None:
        with pytest.raises(UserNotFoundError, match="User record not found"):
            self.service.toggle_can_run_jobs(999, True)


class TestToggleCanRunBgJobs(TestSetup):
    """Tests for toggle_can_run_bg_jobs."""

    def test_toggles_to_true(self) -> None:
        user_record = self.service.create_user("test_user")
        result = self.service.toggle_can_run_bg_jobs(user_record.user_id, True)
        assert bool(result.can_run_bg_jobs) is True

        refreshed = self.service.get(user_record.user_id)
        assert refreshed is not None
        assert bool(refreshed.can_run_bg_jobs) is True

    def test_toggles_to_false(self) -> None:
        user_record = self.service.create_user("test_user")
        result = self.service.toggle_can_run_bg_jobs(user_record.user_id, False)
        assert bool(result.can_run_bg_jobs) is False

        refreshed = self.service.get(user_record.user_id)
        assert refreshed is not None
        assert bool(refreshed.can_run_bg_jobs) is False

    def test_raises_for_missing_user(self) -> None:
        with pytest.raises(UserNotFoundError, match="User record not found"):
            self.service.toggle_can_run_bg_jobs(999, True)
