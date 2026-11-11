"""
Unit tests for domain.models.user module.

Tests for UserRecord.
"""

from datetime import datetime

from src.main_app.database.models import UserRecord


class TestUserRecord:
    """Tests for UserRecord dataclass."""

    def test_create_with_required_fields(self):
        """Test creating UserRecord with required fields."""
        record = UserRecord(
            user_id=1,
            username="TestUser",
        )
        assert record.user_id == 1
        assert record.username == "TestUser"
        assert record.email == ""  # Default value
        assert record.wiki == ""  # Default value
        assert record.created_at is None
        assert record.user_group == "Uncategorized"  # Default value

    def test_create_with_all_fields(self):
        """Test creating UserRecord with all fields."""
        now = datetime.now()
        record = UserRecord(
            user_id=1,
            username="TestUser",
            email="test@example.com",
            wiki="enwiki",
            user_group="Translator",
            created_at=now,
        )
        assert record.user_id == 1
        assert record.username == "TestUser"
        assert record.email == "test@example.com"
        assert record.wiki == "enwiki"
        assert record.user_group == "Translator"
        assert record.created_at == now

    def test_to_dict(self):
        """Test converting UserRecord to dictionary."""
        record = UserRecord(
            user_id=1,
            username="TestUser",
            email="test@example.com",
            wiki="enwiki",
            user_group="Translator",
            created_at=None,
        )
        result = record.to_json()
        assert result == {
            "user_id": 1,
            "username": "TestUser",
            "email": "test@example.com",
            "wiki": "enwiki",
            "user_group": "Translator",
            "created_at": None,
        }
