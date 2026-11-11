"""
Unit tests for domain.models.full_translator module.

Tests for FullTranslatorRecord.
"""

from src.main_app.database.models import FullTranslatorRecord


class TestFullTranslatorRecord:
    """Tests for FullTranslatorRecord dataclass."""

    def test_create_with_required_fields(self):
        """Test creating FullTranslatorRecord with required fields."""
        record = FullTranslatorRecord(id=1, user="TestUser")
        assert record.id == 1
        assert record.user == "TestUser"
        assert record.is_active == 1  # Default value

    def test_create_with_all_fields(self):
        """Test creating FullTranslatorRecord with all fields."""
        record = FullTranslatorRecord(id=1, user="TestUser", is_active=0)
        assert record.id == 1
        assert record.user == "TestUser"
        assert record.is_active == 0

    def test_to_dict(self):
        """Test converting FullTranslatorRecord to dictionary."""
        record = FullTranslatorRecord(id=1, user="TestUser", is_active=1)
        result = record.to_json()
        assert result == {
            "id": 1,
            "user": "TestUser",
            "is_active": 1,
        }
