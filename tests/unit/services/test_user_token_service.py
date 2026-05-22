"""Tests for users store module."""

from unittest.mock import MagicMock, patch

from src.main_app.db.services.user_token_service import (
    UserTokenRecord,
    delete_user_token,
    get_user_token,
    upsert_user_token,
)


class TestUserTokenRecord:
    """Tests for UserTokenRecord dataclass."""

    def test_user_token_record_creation(self):
        """Test creating a UserTokenRecord."""
        record = UserTokenRecord(
            user_id=123,
            username="testuser",
            access_token=b"encrypted_token",
            access_secret=b"encrypted_secret",
        )

        assert record.user_id == 123
        assert record.username == "testuser"
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
            username="anothertest",
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

    @patch("src.main_app.db.models.users.decrypt_value")
    def test_decrypted_success(self, mock_decrypt):
        """Test decrypted method returns decrypted credentials."""
        mock_decrypt.side_effect = ["decrypted_token", "decrypted_secret"]

        record = UserTokenRecord(
            user_id=789,
            username="testuser",
            access_token=b"encrypted_token",
            access_secret=b"encrypted_secret",
        )

        token, secret = record.decrypted()

        assert token == "decrypted_token"
        assert secret == "decrypted_secret"
        mock_decrypt.assert_any_call(b"encrypted_token")
        mock_decrypt.assert_any_call(b"encrypted_secret")


class TestUpsertUserToken:
    """Tests for upsert_user_token function."""
