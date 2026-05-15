"""Tests for users store module."""

from unittest.mock import MagicMock, patch

from src.main_app.sqlalchemy_db.services.user_token_service import (
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

    @patch("src.main_app.sqlalchemy_db.models.users.decrypt_value")
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

    @patch("src.main_app.sqlalchemy_db.services.user_token_service.encrypt_value")
    @patch("src.main_app.sqlalchemy_db.services.user_token_service.get_db")
    def test_upsert_new_token(self, mock_get_db, mock_encrypt):
        """Test upsert_user_token inserts new token."""
        mock_encrypt.side_effect = [b"encrypted_key", b"encrypted_secret"]
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        upsert_user_token(
            user_id=123,
            username="testuser",
            access_key="my_access_key",
            access_secret="my_access_secret",
        )

        mock_encrypt.assert_any_call("my_access_key")
        mock_encrypt.assert_any_call("my_access_secret")
        mock_db.insert_query.assert_called_once()

        # Verify the query contains ON DUPLICATE KEY UPDATE
        call_args = mock_db.insert_query.call_args
        assert "ON DUPLICATE KEY UPDATE" in call_args[0][0]

    @patch("src.main_app.sqlalchemy_db.services.user_token_service.encrypt_value")
    @patch("src.main_app.sqlalchemy_db.services.user_token_service.get_db")
    def test_upsert_updates_existing(self, mock_get_db, mock_encrypt):
        """Test upsert_user_token updates existing token."""
        mock_encrypt.side_effect = [b"new_encrypted_key", b"new_encrypted_secret"]
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        upsert_user_token(
            user_id=456,
            username="existinguser",
            access_key="new_key",
            access_secret="new_secret",
        )

        mock_db.insert_query.assert_called_once()
        # Verify rotated_at is set to CURRENT_TIMESTAMP in the update clause
        call_args = mock_db.insert_query.call_args
        assert "CURRENT_TIMESTAMP" in call_args[0][0]


class TestGetUserToken:
    """Tests for get_user_token function."""

    @patch("src.main_app.sqlalchemy_db.services.user_token_service.get_db")
    def test_get_user_token_found(self, mock_get_db):
        """Test get_user_token returns record when found."""
        mock_db = MagicMock()
        mock_db.fetch_query_safe.return_value = [
            {
                "user_id": 123,
                "username": "testuser",
                "access_token": b"encrypted_token",
                "access_secret": b"encrypted_secret",
                "created_at": "2024-01-01 00:00:00",
                "updated_at": "2024-01-02 00:00:00",
                "last_used_at": "2024-01-03 00:00:00",
                "rotated_at": "2024-01-04 00:00:00",
            }
        ]
        mock_get_db.return_value = mock_db

        result = get_user_token(123)

        assert result is not None
        assert result.user_id == 123
        assert result.username == "testuser"
        assert result.access_token == b"encrypted_token"
        assert result.access_secret == b"encrypted_secret"
        assert result.created_at == "2024-01-01 00:00:00"

    @patch("src.main_app.sqlalchemy_db.services.user_token_service.get_db")
    def test_get_user_token_not_found(self, mock_get_db):
        """Test get_user_token returns None when not found."""
        mock_db = MagicMock()
        mock_db.fetch_query_safe.return_value = []
        mock_get_db.return_value = mock_db

        result = get_user_token(999)

        assert result is None

    @patch("src.main_app.sqlalchemy_db.services.user_token_service.get_db")
    def test_get_user_token_string_id(self, mock_get_db):
        """Test get_user_token converts string ID to int."""
        mock_db = MagicMock()
        mock_db.fetch_query_safe.return_value = []
        mock_get_db.return_value = mock_db

        get_user_token("456")

        # Verify the query was called with integer
        mock_db.fetch_query_safe.assert_called_once()
        call_args = mock_db.fetch_query_safe.call_args
        assert call_args[0][1] == (456,)

    @patch("src.main_app.sqlalchemy_db.services.user_token_service.coerce_bytes")
    @patch("src.main_app.sqlalchemy_db.services.user_token_service.get_db")
    def test_get_user_token_coerces_bytes(self, mock_get_db, mock_coerce):
        """Test get_user_token coerces bytes for token fields."""
        mock_coerce.side_effect = [b"coerced_token", b"coerced_secret"]
        mock_db = MagicMock()
        mock_db.fetch_query_safe.return_value = [
            {
                "user_id": 123,
                "username": "testuser",
                "access_token": "some_token",
                "access_secret": "some_secret",
            }
        ]
        mock_get_db.return_value = mock_db

        result = get_user_token(123)

        assert mock_coerce.call_count == 2
        assert result.access_token == b"coerced_token"
        assert result.access_secret == b"coerced_secret"


class TestDeleteUserToken:
    """Tests for delete_user_token function."""

    @patch("src.main_app.sqlalchemy_db.services.user_token_service.get_db")
    def test_delete_user_token(self, mock_get_db):
        """Test delete_user_token executes delete query."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        delete_user_token(123)

        mock_db.execute_query_safe.assert_called_once_with(
            "DELETE FROM user_tokens WHERE user_id = %s",
            (123,),
        )

    @patch("src.main_app.sqlalchemy_db.services.user_token_service.get_db")
    def test_delete_user_token_different_id(self, mock_get_db):
        """Test delete_user_token with different user ID."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        delete_user_token(999)

        mock_db.execute_query_safe.assert_called_once_with(
            "DELETE FROM user_tokens WHERE user_id = %s",
            (999,),
        )
