"""Unit tests for admin_service module."""

from __future__ import annotations

import pytest

from src.main_app.db.exceptions import DuplicateRecordError, UserNotFoundError
from src.main_app.db.models import AdminUserRecord
from src.main_app.db.models.users import UserRecord
from src.main_app.db.services.admin_service import AdminService
from src.main_app.extensions import db


@pytest.fixture
def user_record() -> UserRecord:
    """Insert and return a fresh UserRecord in the real test DB."""
    record = UserRecord(username="test_user")
    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


@pytest.fixture
def coordinator_record(user_record: UserRecord) -> AdminUserRecord:
    """Insert and return a fresh active AdminUserRecord in the real test DB."""
    record = AdminUserRecord(username=user_record.username, is_active=True)
    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = AdminService()


class TestIsActiveCoordinator(TestSetup):
    def test_active_coordinator(self, coordinator_record: AdminUserRecord) -> None:
        assert self.service.is_active_coordinator(coordinator_record.username) is True

    def test_inactive_coordinator(self, coordinator_record: AdminUserRecord) -> None:
        self.service.set_coordinator_active(coordinator_record.id, False)

        assert self.service.is_active_coordinator(coordinator_record.username) is False

    def test_missing_coordinator(self) -> None:
        assert self.service.is_active_coordinator("testuser") is False


class TestListCoordinators(TestSetup):
    def test_returns_all(self, coordinator_record: AdminUserRecord) -> None:
        result = self.service.list_coordinators()
        assert len(result) == 1
        assert result[0].id == coordinator_record.id
        assert result[0].username == coordinator_record.username

    def test_empty_list(self) -> None:
        result = self.service.list_coordinators()
        assert result == []


class TestGetCoordinatorById(TestSetup):
    def test_found(self, coordinator_record: AdminUserRecord) -> None:
        result = self.service.get_coordinator_by_id(coordinator_record.id)
        assert result.id == coordinator_record.id
        assert result.username == coordinator_record.username

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

    def test_duplicate_raises(self, coordinator_record: AdminUserRecord) -> None:
        with pytest.raises(DuplicateRecordError, match="already exists"):
            self.service.add_coordinator(coordinator_record.username)

    def test_missing_user_raises_user_not_found(self) -> None:
        with pytest.raises(UserNotFoundError, match="does not exist"):
            self.service.add_coordinator("unknown_user")

    def test_success(self, user_record: UserRecord) -> None:
        result = self.service.add_coordinator(user_record.username)
        assert result.username == user_record.username
        assert result.is_active is True

        persisted = self.service.get(result.id)
        assert persisted is not None
        assert persisted.username == user_record.username

    def test_strips_username_before_creating(self, user_record: UserRecord) -> None:
        result = self.service.add_coordinator(f"  {user_record.username}  ")
        assert result.username == user_record.username


class TestSetCoordinatorActive(TestSetup):
    def test_activate(self, coordinator_record: AdminUserRecord) -> None:
        self.service.set_coordinator_active(coordinator_record.id, False)

        result = self.service.set_coordinator_active(coordinator_record.id, True)
        assert result is not None
        assert result.is_active is True

        persisted = self.service.get(coordinator_record.id)
        assert persisted is not None
        assert persisted.is_active is True

    def test_deactivate(self, coordinator_record: AdminUserRecord) -> None:
        result = self.service.set_coordinator_active(coordinator_record.id, False)
        assert result is not None
        assert result.is_active is False

        persisted = self.service.get(coordinator_record.id)
        assert persisted is not None
        assert persisted.is_active is False

    def test_not_found(self) -> None:
        result = self.service.set_coordinator_active(999, True)
        assert result is None


class TestDeleteCoordinator(TestSetup):
    def test_delete_existing_coordinator(self, coordinator_record: AdminUserRecord) -> None:
        result = self.service.delete(coordinator_record.id)
        assert result is True
        db.session.expire_all()
        assert self.service.get(coordinator_record.id) is None

    def test_delete_non_existent_coordinator(self) -> None:
        result = self.service.delete(99999)
        assert result is False
