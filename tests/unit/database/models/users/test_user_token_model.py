"""
Unit tests for domain.models.user_token module.

Tests for UserTokenRecord.
"""

from unittest.mock import MagicMock

import pytest
from src.main_app.database.models import UserRecord, UserTokenRecord


@pytest.fixture
def sample_token_record() -> UserTokenRecord:
    """Fixture for a sample UserTokenRecord."""
    return UserTokenRecord(
        user_id=12345,
        username="TestUser",
        access_token=b"encrypted_token",
        access_secret=b"encrypted_secret",
        created_at="2024-01-01 00:00:00",
        updated_at="2024-01-01 00:00:00",
        last_used_at="2024-01-01 00:00:00",
        rotated_at=None,
    )


class TestUserTokenRecord:
    """Tests for UserTokenRecord dataclass."""

    def test_post_init_coerces_bytes(self) -> None:
        """Test that __post_init__ coerces access fields to bytes."""
        record = UserTokenRecord(
            user_id=1,
            username="Test",
            access_token=bytearray(b"token"),
            access_secret=memoryview(b"secret"),
        )
        assert isinstance(record.access_token, bytes)
        assert isinstance(record.access_secret, bytes)

    def test_user_token_record_creation(self):
        """Test creating a UserTokenRecord."""
        record = UserTokenRecord(
            user_id=123,
            access_token=b"encrypted_token",
            access_secret=b"encrypted_secret",
        )

        assert record.user_id == 123
        assert record.access_token == b"encrypted_token"
        assert record.access_secret == b"encrypted_secret"
        assert record.created_at is None
        assert record.updated_at is None
        assert record.last_used_at is None
        assert record.rotated_at is None

    def test_user_token_record_with_timestamps(self):
        """Test creating a UserTokenRecord with timestamps."""
        record = UserTokenRecord(
            user_id=456,
            access_token=b"token",
            access_secret=b"secret",
            created_at="2024-01-01 00:00:00",
            updated_at="2024-01-02 00:00:00",
            last_used_at="2024-01-03 00:00:00",
            rotated_at="2024-01-04 00:00:00",
        )

        assert record.created_at == "2024-01-01 00:00:00"
        assert record.updated_at == "2024-01-02 00:00:00"
        assert record.last_used_at == "2024-01-03 00:00:00"
        assert record.rotated_at == "2024-01-04 00:00:00"

    def test_decrypted_success(self):
        """Test decrypted method returns decrypted credentials."""
        record = UserTokenRecord(
            user_id=789,
            access_token=b"encrypted_token",
            access_secret=b"encrypted_secret",
        )

        assert record.access_token == b"encrypted_token"
        assert record.access_secret == b"encrypted_secret"

    def test_user_token_record(self, sqlite_db) -> None:

        user = UserRecord(user_id=123, username="model_token_user")
        sqlite_db.session.add(user)
        sqlite_db.session.commit()

        token = b"access_token_val"
        secret = b"access_secret_val"

        user_token = UserTokenRecord(user_id=123, access_token=token, access_secret=secret)
        sqlite_db.session.add(user_token)
        sqlite_db.session.commit()

        assert user_token.user_id == 123
        assert user_token.user.username == "model_token_user"

    def test_user_token_record_validation(self) -> None:

        user = UserRecord(user_id=456, username="model_validation_user")
        # sqlite_db.session.add(user)
        # sqlite_db.session.commit()

        user_token = UserTokenRecord(user_id=456, access_token=bytearray(b"token"), access_secret=memoryview(b"secret"))
        assert isinstance(user_token.access_token, bytes)
        assert isinstance(user_token.access_secret, bytes)
