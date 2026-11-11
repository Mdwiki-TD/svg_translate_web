"""
Unit tests for domain.models.users_no_inprocess module.

Tests for UsersNoInprocessRecord.
"""

from src.main_app.database.models import UsersNoInprocessRecord


class TestUsersNoInprocessRecord:
    """Tests for UsersNoInprocessRecord dataclass."""

    def test_create_with_required_fields(self):
        """Test creating UsersNoInprocessRecord with required fields."""
        record = UsersNoInprocessRecord(id=1, user="TestUser")
        assert record.id == 1
        assert record.user == "TestUser"
        assert record.is_active == 1  # Default value

    def test_create_with_all_fields(self):
        """Test creating UsersNoInprocessRecord with all fields."""
        record = UsersNoInprocessRecord(id=1, user="TestUser", is_active=0)
        assert record.id == 1
        assert record.user == "TestUser"
        assert record.is_active == 0

    def test_to_dict(self):
        """Test converting UsersNoInprocessRecord to dictionary."""
        record = UsersNoInprocessRecord(id=1, user="TestUser", is_active=1)
        result = record.to_json()
        assert result == {
            "id": 1,
            "user": "TestUser",
            "is_active": 1,
        }
