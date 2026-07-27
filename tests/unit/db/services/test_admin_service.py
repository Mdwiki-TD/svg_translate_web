"""Unit tests for admin_service module."""

from __future__ import annotations

import pytest

from src.main_app.db.exceptions import DuplicateRecordError, UserNotFoundError
from src.main_app.db.services.admin_service import AdminService
from src.main_app.db.services.users_service import UsersService

class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.user_service = UsersService()
        self.service = AdminService()

        self.user_record = self.user_service.create(username="test_user")
        self.coordinator_record = self.service.create(username=self.user_record.username, is_active=True)

class TestIsActiveCoordinator(TestSetup):
    def test_active_coordinator(self) -> None:
        assert self.service.is_active_coordinator(self.coordinator_record.username) is True

    def test_inactive_coordinator(self) -> None:
        self.service.set_coordinator_active(self.coordinator_record.id, False)

        assert self.service.is_active_coordinator(self.coordinator_record.username) is False

    def test_missing_coordinator(self) -> None:
        assert self.service.is_active_coordinator("testuser") is False


class TestListCoordinators(TestSetup):
    def test_returns_all(self) -> None:
        result = self.service.list_coordinators()
        assert len(result) == 1
        assert result[0].id == self.coordinator_record.id
        assert result[0].username == self.coordinator_record.username


class TestListCoordinators2:
    def test_empty_list(self) -> None:
        service = AdminService()
        result = service.list_coordinators()
        assert result == []


class TestGetCoordinatorById(TestSetup):
    def test_found(self) -> None:
        result = self.service.get_coordinator_by_id(self.coordinator_record.id)
        assert result.id == self.coordinator_record.id
        assert result.username == self.coordinator_record.username

    def test_not_found_raises(self) -> None:
        with pytest.raises(LookupError, match="not found"):
            self.service.get_coordinator_by_id(999)


class TestAddCoordinator(TestSetup):
    def test_empty_username_raises(self) -> None:
        with pytest.raises(ValueError, match="Username is required"):
            self.service.add_coordinator("")

    def test_whitespace_username_raises(self) -> None:
        with pytest.raises(ValueError, match="Username is required"):
            self.service.add_coordinator("   ")

    def test_duplicate_raises(self) -> None:
        with pytest.raises(DuplicateRecordError, match="already exists"):
            self.service.add_coordinator(self.coordinator_record.username)

    def test_missing_user_raises_user_not_found(self) -> None:
        with pytest.raises(UserNotFoundError, match="does not exist"):
            self.service.add_coordinator("unknown_user")

    def test_success(self) -> None:
        user_record = self.user_service.create(username="test_user1")
        result = self.service.add_coordinator(user_record.username)
        assert result.username == user_record.username
        assert result.is_active is True

        persisted = self.service.get(result.id)
        assert persisted is not None
        assert persisted.username == user_record.username

    def test_strips_username_before_creating(self) -> None:
        user_record = self.user_service.create(username="test_user2")
        result = self.service.add_coordinator("  test_user2  ")
        assert result.username == user_record.username


class TestSetCoordinatorActive(TestSetup):
    def test_activate(self) -> None:
        self.service.set_coordinator_active(self.coordinator_record.id, False)

        result = self.service.set_coordinator_active(self.coordinator_record.id, True)
        assert result is not None
        assert result.is_active is True

        persisted = self.service.get(self.coordinator_record.id)
        assert persisted is not None
        assert persisted.is_active is True

    def test_deactivate(self) -> None:
        result = self.service.set_coordinator_active(self.coordinator_record.id, False)
        assert result is not None
        assert result.is_active is False

        persisted = self.service.get(self.coordinator_record.id)
        assert persisted is not None
        assert persisted.is_active is False

    def test_not_found(self) -> None:
        result = self.service.set_coordinator_active(999, True)
        assert result is None


class TestDeleteCoordinator(TestSetup):
    def test_delete_existing_coordinator(self) -> None:
        result = self.service.delete(self.coordinator_record.id)
        assert result is True
        self.service.expire_all()
        assert self.service.get(self.coordinator_record.id) is None

    def test_delete_non_existent_coordinator(self) -> None:
        result = self.service.delete(99999)
        assert result is False
