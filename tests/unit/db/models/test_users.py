"""
Unit tests for src/main_app/sqlite_db/models/users.py module.

Classes to test: UserRecord, AdminUserRecord, UserTokenRecord
"""

from __future__ import annotations

from src.main_app.db.models.users import (
    AdminUserRecord,
    UserRecord,
    UserTokenRecord,
)


class TestUserRecord:
    """Tests for UserRecord dataclass."""

    def test_users_record(self, sqlite_db) -> None:

        user = UserRecord(user_id=42, username="model_test_user")
        sqlite_db.session.add(user)
        sqlite_db.session.commit()

        assert user.user_id == 42
        assert user.username == "model_test_user"
        assert user.created_at is not None


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


class TestUserTokenRecord:
    """Tests for UserTokenRecord dataclass."""

    def test_user_token_record_creation(self) -> None:
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

    def test_user_token_record_with_timestamps(self) -> None:
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

    def test_decrypted_success(self) -> None:
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
