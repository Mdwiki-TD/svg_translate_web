"""
Unit tests for src/main_app/database/models/admin_users.py module.

Classes to test: AdminUserRecord

TODO: write tests
"""

from src.main_app.database.models import UserRecord
from src.main_app.database.models.users import AdminUserRecord


class TestAdminUserRecord:
    """Tests for AdminUserRecord dataclass."""

    def test_admin_user_record(self, sqlite_db) -> None:

        user = UserRecord(user_id=1, username="model_admin_user")
        sqlite_db.session.add(user)
        sqlite_db.session.commit()

        admin = AdminUserRecord(username="model_admin_user", is_active=True)
        sqlite_db.session.add(admin)
        sqlite_db.session.commit()

        assert admin.id is not None
        assert admin.username == "model_admin_user"
        assert admin.is_active is True

    def test_admin_record_initialization(self, sqlite_db) -> None:
        """Test AdminUserRecord initialization with required fields."""
        rec = AdminUserRecord(id=1, username="testuser", is_active=True)

        assert rec.id == 1
        assert rec.username == "testuser"
        assert rec.is_active is True
        assert rec.created_at is None
        assert rec.updated_at is None

    def test_admin_record_with_all_fields(self, sqlite_db) -> None:
        """Test AdminUserRecord initialization with all fields."""
        rec = AdminUserRecord(
            id=1, username="testuser", is_active=True, created_at="2023-01-01", updated_at="2023-01-02"
        )

        assert rec.id == 1
        assert rec.username == "testuser"
        assert rec.is_active is True
        assert rec.created_at == "2023-01-01"
        assert rec.updated_at == "2023-01-02"

    def test_admin_record_inactive(self, sqlite_db) -> None:
        """Test AdminUserRecord with inactive user."""
        rec = AdminUserRecord(id=1, username="testuser", is_active=False)

        assert rec.id == 1
        assert rec.username == "testuser"
        assert rec.is_active is False
        assert rec.created_at is None
        assert rec.updated_at is None

    def test_admin_record_to_dict(self, sqlite_db) -> None:
        """Test conversion to dictionary."""
        rec = AdminUserRecord(
            id=1, username="testuser", is_active=True, created_at="2023-01-01", updated_at="2023-01-02"
        )

        result = rec.to_json()

        expected = {
            "id": 1,
            "username": "testuser",
            "is_active": True,
            "created_at": "2023-01-01",
            "updated_at": "2023-01-02",
        }

        assert result == expected

    def test_admin_record_to_dict_with_none_values(self, sqlite_db) -> None:
        """Test conversion to dictionary with None values."""
        rec = AdminUserRecord(id=1, username="testuser", is_active=True, created_at=None, updated_at=None)

        result = rec.to_json()

        expected = {"id": 1, "username": "testuser", "is_active": True, "created_at": None, "updated_at": None}

        assert result == expected
