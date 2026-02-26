"""Tests for users store module."""

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.users.store import (
    UserTokenRecord,
    _coerce_bytes,
    _current_ts,
    delete_user_token,
    ensure_user_token_table,
    get_user_token,
    mark_token_used,
    upsert_user_token,
)


class TestCurrentTimestamp:
    """Tests for _current_ts function."""

    @patch("src.main_app.users.store.datetime.datetime")
    def test_current_ts_format(self, mock_datetime):
        """Test that _current_ts returns properly formatted timestamp."""
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2024-01-15 10:30:45"
        mock_datetime.now.return_value = mock_now

        result = _current_ts()

        assert result == "2024-01-15 10:30:45"
        mock_datetime.now.assert_called_once()


class TestCoerceBytes:
    """Tests for _coerce_bytes function."""

    def test_coerce_bytes_with_bytes(self):
        """Test _coerce_bytes with bytes input."""
        input_bytes = b"test_data"
        result = _coerce_bytes(input_bytes)
        assert result == input_bytes

    def test_coerce_bytes_with_bytearray(self):
        """Test _coerce_bytes with bytearray input."""
        input_bytearray = bytearray(b"test_data")
        result = _coerce_bytes(input_bytearray)
        assert result == b"test_data"
        assert isinstance(result, bytes)

    def test_coerce_bytes_with_memoryview(self):
        """Test _coerce_bytes with memoryview input."""
        input_memoryview = memoryview(b"test_data")
        result = _coerce_bytes(input_memoryview)
        assert result == b"test_data"
        assert isinstance(result, bytes)

    def test_coerce_bytes_with_invalid_type(self):
        """Test _coerce_bytes raises TypeError for invalid input."""
        with pytest.raises(TypeError, match="Expected bytes-compatible value"):
            _coerce_bytes("string_not_bytes")

    def test_coerce_bytes_with_int(self):
        """Test _coerce_bytes raises TypeError for integer input."""
        with pytest.raises(TypeError, match="Expected bytes-compatible value"):
            _coerce_bytes(123)

    def test_coerce_bytes_with_none(self):
        """Test _coerce_bytes raises TypeError for None input."""
        with pytest.raises(TypeError, match="Expected bytes-compatible value"):
            _coerce_bytes(None)


class TestMarkTokenUsed:
    """Tests for mark_token_used function."""

    @patch("src.main_app.users.store.get_db")
    def test_mark_token_used_success(self, mock_get_db):
        """Test mark_token_used updates timestamp successfully."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mark_token_used(123)

        mock_db.execute_query.assert_called_once_with(
            "UPDATE user_tokens SET last_used_at = CURRENT_TIMESTAMP WHERE user_id = %s",
            (123,),
        )

    @patch("src.main_app.users.store.logger")
    @patch("src.main_app.users.store.get_db")
    def test_mark_token_used_failure(self, mock_get_db, mock_logger):
        """Test mark_token_used logs error on failure."""
        mock_db = MagicMock()
        mock_db.execute_query.side_effect = Exception("DB Error")
        mock_get_db.return_value = mock_db

        mark_token_used(456)

        mock_logger.exception.assert_called_once()
        assert "Failed to update last_used_at" in mock_logger.exception.call_args[0][0]


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

    @patch("src.main_app.users.store.mark_token_used")
    @patch("src.main_app.users.store.decrypt_value")
    def test_decrypted_success(self, mock_decrypt, mock_mark_used):
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
        mock_mark_used.assert_called_once_with(789)

    @patch("src.main_app.users.store.mark_token_used")
    @patch("src.main_app.users.store.decrypt_value")
    def test_decrypted_calls_mark_token_used(self, mock_decrypt, mock_mark_used):
        """Test decrypted method marks token as used."""
        mock_decrypt.return_value = "decrypted"

        record = UserTokenRecord(
            user_id=999,
            username="testuser",
            access_token=b"token",
            access_secret=b"secret",
        )

        record.decrypted()

        mock_mark_used.assert_called_once_with(999)


class TestEnsureUserTokenTable:
    """Tests for ensure_user_token_table function."""

    @patch("src.main_app.users.store.has_db_config")
    def test_ensure_table_no_config(self, mock_has_config):
        """Test ensure_user_token_table returns early if no DB config."""
        mock_has_config.return_value = False

        with patch("src.main_app.users.store.get_db") as mock_get_db:
            ensure_user_token_table()
            mock_get_db.assert_not_called()

    @patch("src.main_app.users.store.get_db")
    @patch("src.main_app.users.store.has_db_config")
    def test_ensure_table_creates_table(self, mock_has_config, mock_get_db):
        """Test ensure_user_token_table creates table and index."""
        mock_has_config.return_value = True
        mock_db = MagicMock()
        mock_db.fetch_query_safe.return_value = []  # No existing index
        mock_get_db.return_value = mock_db

        ensure_user_token_table()

        # Should execute table creation
        mock_db.execute_query_safe.assert_called()
        calls = mock_db.execute_query_safe.call_args_list
        assert any(
            "CREATE TABLE IF NOT EXISTS user_tokens" in str(call) for call in calls
        )

    @patch("src.main_app.users.store.get_db")
    @patch("src.main_app.users.store.has_db_config")
    def test_ensure_table_existing_index(self, mock_has_config, mock_get_db):
        """Test ensure_user_token_table skips index creation if exists."""
        mock_has_config.return_value = True
        mock_db = MagicMock()
        mock_db.fetch_query_safe.return_value = [
            {"Key_name": "idx_user_tokens_username"}
        ]
        mock_get_db.return_value = mock_db

        ensure_user_token_table()

        # Should only execute table creation, not index creation
        calls = mock_db.execute_query_safe.call_args_list
        assert len([c for c in calls if "CREATE INDEX" in str(c)]) == 0


class TestUpsertUserToken:
    """Tests for upsert_user_token function."""

    @patch("src.main_app.users.store._current_ts")
    @patch("src.main_app.users.store.encrypt_value")
    @patch("src.main_app.users.store.get_db")
    def test_upsert_new_token(self, mock_get_db, mock_encrypt, mock_current_ts):
        """Test upsert_user_token inserts new token."""
        mock_current_ts.return_value = "2024-01-15 10:30:45"
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
        mock_db.execute_query_safe.assert_called_once()

        # Verify the query contains ON DUPLICATE KEY UPDATE
        call_args = mock_db.execute_query_safe.call_args
        assert "ON DUPLICATE KEY UPDATE" in call_args[0][0]

    @patch("src.main_app.users.store._current_ts")
    @patch("src.main_app.users.store.encrypt_value")
    @patch("src.main_app.users.store.get_db")
    def test_upsert_updates_existing(self, mock_get_db, mock_encrypt, mock_current_ts):
        """Test upsert_user_token updates existing token."""
        mock_current_ts.return_value = "2024-01-15 10:30:45"
        mock_encrypt.side_effect = [b"new_encrypted_key", b"new_encrypted_secret"]
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        upsert_user_token(
            user_id=456,
            username="existinguser",
            access_key="new_key",
            access_secret="new_secret",
        )

        mock_db.execute_query_safe.assert_called_once()
        # Verify rotated_at is set to CURRENT_TIMESTAMP in the update clause
        call_args = mock_db.execute_query_safe.call_args
        assert "CURRENT_TIMESTAMP" in call_args[0][0]


class TestGetUserToken:
    """Tests for get_user_token function."""

    @patch("src.main_app.users.store.get_db")
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

    @patch("src.main_app.users.store.get_db")
    def test_get_user_token_not_found(self, mock_get_db):
        """Test get_user_token returns None when not found."""
        mock_db = MagicMock()
        mock_db.fetch_query_safe.return_value = []
        mock_get_db.return_value = mock_db

        result = get_user_token(999)

        assert result is None

    @patch("src.main_app.users.store.get_db")
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

    @patch("src.main_app.users.store._coerce_bytes")
    @patch("src.main_app.users.store.get_db")
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

    @patch("src.main_app.users.store.get_db")
    def test_delete_user_token(self, mock_get_db):
        """Test delete_user_token executes delete query."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        delete_user_token(123)

        mock_db.execute_query_safe.assert_called_once_with(
            "DELETE FROM user_tokens WHERE user_id = %s",
            (123,),
        )

    @patch("src.main_app.users.store.get_db")
    def test_delete_user_token_different_id(self, mock_get_db):
        """Test delete_user_token with different user ID."""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        delete_user_token(999)

        mock_db.execute_query_safe.assert_called_once_with(
            "DELETE FROM user_tokens WHERE user_id = %s",
            (999,),
        )
