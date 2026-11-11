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
        assert record.created_at is None

    def test_create_with_all_fields(self):
        """Test creating UserRecord with all fields."""
        now = datetime.now()
        record = UserRecord(
            user_id=1,
            username="TestUser",
            created_at=now,
        )
        assert record.user_id == 1
        assert record.username == "TestUser"
        assert record.created_at == now

    def test_to_dict(self):
        """Test converting UserRecord to dictionary."""
        record = UserRecord(
            user_id=1,
            username="TestUser",
            created_at=None,
        )
        result = record.to_json()
        assert result == {
            "user_id": 1,
            "username": "TestUser",
            "can_run_jobs": None,
            "can_run_bg_jobs": None,
            "created_at": None,
        }
