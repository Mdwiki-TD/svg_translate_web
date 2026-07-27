"""Unit tests for admin_service module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from src.main_app.db.exceptions import DuplicateRecordError, UserNotFoundError
from src.main_app.db.models import AdminUserRecord
from src.main_app.db.models.users import UserRecord
from src.main_app.db.services.admin_service import AdminService


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        self.service = AdminService()
        self.mock_dbsession = MagicMock()
        self.service.session = self.mock_dbsession


class TestIsActiveCoordinator(TestSetup):
    def test_active_coordinator(self):
        mock_record = MagicMock()

        self.mock_dbsession.query.return_value.filter.return_value.first.return_value = mock_record

        assert self.service.is_active_coordinator("testuser") is True

    def test_inactive_coordinator(self):

        self.mock_dbsession.query.return_value.filter.return_value.first.return_value = None

        assert self.service.is_active_coordinator("testuser") is False

    def test_exception_returns_false(self):

        self.mock_dbsession.query.side_effect = Exception("DB error")

        assert self.service.is_active_coordinator("testuser") is False


class TestListCoordinators(TestSetup):
    def test_returns_all(self):

        self.mock_dbsession.query.return_value.all.return_value = ["record1", "record2"]

        result = self.service.list_coordinators()
        assert result == ["record1", "record2"]

    def test_empty_list(self):

        self.mock_dbsession.query.return_value.all.return_value = []

        result = self.service.list_coordinators()
        assert result == []


class TestGetCoordinatorById(TestSetup):
    def test_found(self):
        mock_record = MagicMock()
        mock_record.id = 1
        self.mock_dbsession.get.return_value = mock_record
        result = self.service.get_coordinator_by_id(1)
        assert result.id == 1

    def test_not_found_raises(self):
        self.mock_dbsession.get.return_value = None
        with pytest.raises(LookupError, match="not found"):
            self.service.get_coordinator_by_id(999)


class TestAddCoordinator(TestSetup):
    def test_empty_username_raises(self):
        with pytest.raises(ValueError, match="Username is required"):
            self.service.add_coordinator("")

    def test_whitespace_username_raises(self):
        with pytest.raises(ValueError, match="Username is required"):
            self.service.add_coordinator("   ")

    def test_duplicate_raises(self):
        mock_record = MagicMock()

        self.mock_dbsession.query.return_value.filter.return_value.first.return_value = mock_record

        with pytest.raises(DuplicateRecordError, match="already exists"):
            self.service.add_coordinator("existing_user")

    def test_integrity_error_raises_user_not_found(self):

        self.mock_dbsession.query.return_value.filter.return_value.first.return_value = None
        self.mock_dbsession.commit.side_effect = IntegrityError("mock", "orig", "a foreign key constraint fails")

        with pytest.raises(UserNotFoundError, match="does not exist"):
            self.service.add_coordinator("unknown_user")

    def test_success(self):

        self.mock_dbsession.query.return_value.filter.return_value.first.return_value = None
        self.mock_dbsession.commit.return_value = None

        result = self.service.add_coordinator("new_user")
        assert result.username == "new_user"
        assert result.is_active is True


class TestSetCoordinatorActive(TestSetup):
    def test_activate(self):
        mock_record = MagicMock()
        mock_record.is_active = False

        self.mock_dbsession.query.return_value.filter.return_value.first.return_value = mock_record

        result = self.service.set_coordinator_active(1, True)
        assert result is not None
        assert result.is_active is True

    def test_deactivate(self):
        mock_record = MagicMock()
        mock_record.is_active = True

        self.mock_dbsession.query.return_value.filter.return_value.first.return_value = mock_record

        result = self.service.set_coordinator_active(1, False)
        assert result is not None
        assert result.is_active is False

    def test_not_found(self):

        self.mock_dbsession.query.return_value.filter.return_value.first.return_value = None

        result = self.service.set_coordinator_active(999, True)
        assert result is None


class TestDeleteCoordinator:
    def test_delete_existing_coordinator(self, mock_app, setup_db):
        service = AdminService()
        with mock_app.app_context():
            user = UserRecord(username="admin_user", user_id=401)
            service.session.add(user)
            service.session.commit()

            record = AdminUserRecord(username="admin_user", is_active=True)
            service.session.add(record)
            service.session.commit()

            result = service.delete(record.id)
            assert result is True
            service.session.expire_all()
            assert service.session.get(AdminUserRecord, record.id) is None

    def test_delete_non_existent_coordinator(self, mock_app, setup_db):
        service = AdminService()
        with mock_app.app_context():
            result = service.delete(99999)
            assert result is False
