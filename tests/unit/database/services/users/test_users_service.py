"""Tests for users_service module."""

from __future__ import annotations

import pytest
from src.main_app.database.exceptions import DuplicateRecordError, RecordNotFoundError
from src.main_app.database.models import UserRecord
from src.main_app.database.services.users.users_service import UsersService

pytestmark = pytest.mark.unit


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = UsersService()


class TestUsersService(TestSetup):
    """Tests for UsersService class."""

    def test_user_workflow(self) -> None:
        # Create a user with optional metadata fields and verify retrieval.
        user = self.service.create_user(
            "Wiki_User",
        )
        assert user.username == "Wiki_User"

        by_id = self.service.get_user(user.user_id)
        assert by_id is not None
        assert by_id.username == "Wiki_User"

        by_name = self.service.get_user_by_username("Wiki_User")
        assert by_name is not None
        assert by_name.user_id == user.user_id

        assert any(x.username == "Wiki_User" for x in self.service.list_users())

        # Update user attributes and confirm persistence.
        updated = self.service.update_by_id(user.user_id, {"can_run_jobs": "1"})
        assert updated is not None
        assert updated.can_run_jobs == 1
        assert self.service.get_user_by_username("Wiki_User") is not None

        # Delete the user and verify removal.
        deleted = self.service.delete(user.user_id)
        assert deleted is True
        assert self.service.get_user(user.user_id) is None


class TestListUsers(TestSetup):
    """Tests for list_users method."""

    def test_returns_all_users(self) -> None:
        user_a = self.service.create_user("Wiki_Admin")
        user_b = self.service.create_user("Wiki_Editor")
        result = self.service.list_users()
        usernames = {u.username for u in result}
        assert len(result) >= 2
        assert {user_a.username, user_b.username}.issubset(usernames)

    def test_returns_empty_when_no_users(self) -> None:
        assert self.service.list_users() == []


class TestGetUser(TestSetup):
    """Tests for get_user method."""

    def test_returns_user_by_valid_id(self) -> None:
        user = self.service.create_user("ContributorA")
        result = self.service.get_user(user.user_id)
        assert isinstance(result, UserRecord)
        assert result.user_id == user.user_id
        assert result.username == "ContributorA"

    def test_returns_none_for_zero_id(self) -> None:
        assert self.service.get_user(0) is None

    def test_returns_none_for_none_id(self) -> None:
        assert self.service.get_user(None) is None  # type: ignore[arg-type]

    def test_returns_none_for_non_existent_id(self) -> None:
        assert self.service.get_user(9999) is None


class TestGetUserByUsername(TestSetup):
    """Tests for get_user_by_username method."""

    def test_returns_user_by_existing_username(self) -> None:
        user = self.service.create_user("Linguist_Specialist")
        result = self.service.get_user_by_username("Linguist_Specialist")
        assert result is not None
        assert result.user_id == user.user_id
        assert result.username == "Linguist_Specialist"

    def test_returns_none_for_empty_username(self) -> None:
        assert self.service.get_user_by_username("") is None
        assert self.service.get_user_by_username("  ") is None

    def test_returns_none_for_none_username(self) -> None:
        assert self.service.get_user_by_username(None) is None  # type: ignore[arg-type]

    def test_returns_none_for_non_existent_username(self) -> None:
        assert self.service.get_user_by_username("Ghost") is None


class TestCreateUser(TestSetup):
    """Tests for create_user method."""

    def test_creates_new_user_with_fields(self) -> None:
        record = self.service.create_user(
            "New_Researcher",
        )
        assert record is not None
        assert record.user_id is not None
        assert record.username == "New_Researcher"

        persisted = self.service.get_by(username="New_Researcher")
        assert persisted is not None
        assert persisted.user_id == record.user_id

    def test_raises_when_user_exists(self) -> None:
        user_record = self.service.create_user("test_user")
        assert user_record is not None

        with pytest.raises(DuplicateRecordError, match="User test_user already exists"):
            self.service.create_user("test_user")

    def test_raises_error_if_no_username(self) -> None:
        with pytest.raises(ValueError, match="Username is required"):
            self.service.create_user("")


class TestDeleteUser(TestSetup):
    """Tests for delete method."""

    def test_deletes_existing_user(self) -> None:
        user = self.service.create_user("Temporary_Account")
        deleted = self.service.delete(user.user_id)
        assert deleted is True
        assert self.service.get_user(user.user_id) is None

    def test_returns_false_when_not_found(self) -> None:
        assert self.service.delete(9999) is False


class TestToggleCanRunJobs(TestSetup):
    """Tests for toggling can_run_jobs via update_by_id."""

    def test_toggles_to_true(self) -> None:
        user_record = self.service.create_user("test_user")
        assert user_record is not None

        result = self.service.update_by_id(user_record.user_id, {"can_run_jobs": True})
        assert bool(result.can_run_jobs) is True

        refreshed = self.service.get(user_record.user_id)
        assert refreshed is not None
        assert bool(refreshed.can_run_jobs) is True

    def test_toggles_to_false(self) -> None:
        user_record = self.service.create_user("test_user")
        assert user_record is not None

        result = self.service.update_by_id(user_record.user_id, {"can_run_jobs": False})
        assert bool(result.can_run_jobs) is False

        refreshed = self.service.get(user_record.user_id)
        assert refreshed is not None
        assert bool(refreshed.can_run_jobs) is False

    def test_raises_for_missing_user(self) -> None:
        with pytest.raises(RecordNotFoundError, match="UserRecord with id=999 not found not found"):
            self.service.update_by_id(999, {"can_run_jobs": False})


class TestToggleCanRunBgJobs(TestSetup):
    """Tests for toggling can_run_bg_jobs via update_by_id."""

    def test_toggles_to_true(self) -> None:
        user_record = self.service.create_user("test_user")
        assert user_record is not None

        result = self.service.update_by_id(user_record.user_id, {"can_run_bg_jobs": True})
        assert bool(result.can_run_bg_jobs) is True

        refreshed = self.service.get(user_record.user_id)
        assert refreshed is not None
        assert bool(refreshed.can_run_bg_jobs) is True

    def test_toggles_to_false(self) -> None:
        user_record = self.service.create_user("test_user")
        assert user_record is not None

        result = self.service.update_by_id(user_record.user_id, {"can_run_bg_jobs": False})
        assert bool(result.can_run_bg_jobs) is False

        refreshed = self.service.get(user_record.user_id)
        assert refreshed is not None
        assert bool(refreshed.can_run_bg_jobs) is False

    def test_raises_for_missing_user(self) -> None:
        with pytest.raises(RecordNotFoundError, match="UserRecord with id=999 not found not found"):
            self.service.update_by_id(999, {"can_run_bg_jobs": False})
