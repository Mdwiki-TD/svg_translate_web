"""
Unit tests for src/main_app/db/services/admin_service.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from src.main_app.db.exceptions import DuplicateUserError, UserNotFoundError
from src.main_app.db.models import AdminUserRecord
from src.main_app.db.models.users import UserRecord
from src.main_app.db.services.admin_service import (
    AdminService,
    add_coordinator,
    get_coordinator_by_id,
    is_active_coordinator,
    list_coordinators,
    set_coordinator_active,
)


class TestIsActiveCoordinator:
    def test_active_coordinator(self):
        mock_record = MagicMock()
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_record
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            assert is_active_coordinator("testuser") is True

    def test_inactive_coordinator(self):
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            assert is_active_coordinator("testuser") is False

    def test_exception_returns_false(self):
        mock_db = MagicMock()
        mock_db.session.query.side_effect = Exception("DB error")
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            assert is_active_coordinator("testuser") is False


class TestListCoordinators:
    def test_returns_all(self):
        mock_db = MagicMock()
        mock_db.session.query.return_value.all.return_value = ["record1", "record2"]
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            result = list_coordinators()
            assert result == ["record1", "record2"]

    def test_empty_list(self):
        mock_db = MagicMock()
        mock_db.session.query.return_value.all.return_value = []
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            result = list_coordinators()
            assert result == []


class TestGetCoordinatorById:
    def test_found(self):
        mock_record = MagicMock()
        mock_record.id = 1
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_record
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            result = get_coordinator_by_id(1)
            assert result.id == 1

    def test_not_found_raises(self):
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            with pytest.raises(LookupError, match="not found"):
                get_coordinator_by_id(999)


class TestAddCoordinator:
    def test_empty_username_raises(self):
        with patch("src.main_app.db.services.admin_service.db"):
            with pytest.raises(ValueError, match="Username is required"):
                add_coordinator("")

    def test_whitespace_username_raises(self):
        with patch("src.main_app.db.services.admin_service.db"):
            with pytest.raises(ValueError, match="Username is required"):
                add_coordinator("   ")

    def test_duplicate_raises(self):
        mock_record = MagicMock()
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_record
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            with pytest.raises(DuplicateUserError, match="already exists"):
                add_coordinator("existing_user")

    def test_integrity_error_raises_user_not_found(self):
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        mock_db.session.commit.side_effect = IntegrityError("mock", "orig", "a foreign key constraint fails")
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            with pytest.raises(UserNotFoundError, match="does not exist"):
                add_coordinator("unknown_user")

    def test_success(self):
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        mock_db.session.commit.return_value = None
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            result = add_coordinator("new_user")
            assert result.username == "new_user"
            assert result.is_active is True


class TestSetCoordinatorActive:
    def test_activate(self):
        mock_record = MagicMock()
        mock_record.is_active = False
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_record
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            result = set_coordinator_active(1, True)
            assert result.is_active is True

    def test_deactivate(self):
        mock_record = MagicMock()
        mock_record.is_active = True
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_record
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            result = set_coordinator_active(1, False)
            assert result.is_active is False

    def test_not_found(self):
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            result = set_coordinator_active(999, True)
            assert result is None


class TestDeleteCoordinator:
    def test_delete_existing_coordinator(self, mock_app, setup_db):
        from src.main_app.extensions import db as _db

        with mock_app.app_context():
            # AdminUserRecord FK → UserRecord, so create a user first
            user = UserRecord(username="admin_user", user_id=401)
            _db.session.add(user)
            _db.session.commit()

            record = AdminUserRecord(username="admin_user", is_active=True)
            _db.session.add(record)
            _db.session.commit()

            result = AdminService().delete(record.id)
            assert result is True
            _db.session.expire_all()
            assert _db.session.get(AdminUserRecord, record.id) is None

    def test_delete_non_existent_coordinator(self, mock_app, setup_db):
        with mock_app.app_context():
            result = AdminService().delete(99999)
            assert result is False
