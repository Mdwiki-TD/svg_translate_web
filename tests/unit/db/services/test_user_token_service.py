"""Tests for user_token_service module."""

from __future__ import annotations

from unittest.mock import MagicMock

from flask.app import Flask

from src.main_app.db.models import UserTokenRecord
from src.main_app.db.services.user_token_service import UserTokenService
from src.main_app.db.services.users_service import UsersService


def test_delete_user_cascades(mock_app: Flask) -> None:
    with mock_app.app_context():
        user = UsersService().create_user("svc_dave")
        UserTokenService().upsert_user_token(user_id=user.user_id, access_key="k", access_secret="s")
        assert UserTokenService().get_user_token(user.user_id) is not None


def test_upsert_get_delete_user_token(mock_app: Flask) -> None:
    with mock_app.app_context():
        user = UsersService().create_user("svc_eve")
        UserTokenService().upsert_user_token(user_id=user.user_id, access_key="key", access_secret="secret")

        token_record = UserTokenService().get_user_token(user.user_id)
        assert token_record is not None
        assert token_record.access_token is not None
        assert token_record.access_secret is not None

        UserTokenService().upsert_user_token(user_id=user.user_id, access_key="new_key", access_secret="new_secret")
        token_record = UserTokenService().get_user_token(user.user_id)

        UserTokenService().delete(user.user_id)
        assert UserTokenService().get_user_token(user.user_id) is None


class TestUserTokenRecord:
    """Tests for UserTokenRecord dataclass."""

    def test_user_token_record_creation(self):
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
        record = UserTokenRecord(
            user_id=789,
            access_token=b"encrypted_token",
            access_secret=b"encrypted_secret",
        )

        assert record.access_token == b"encrypted_token"
        assert record.access_secret == b"encrypted_secret"


class TestGetAuthenticatedUserToken:
    """Tests for get_authenticated_user_token."""

    def test_returns_token_when_user_exists(self, monkeypatch):
        mock_token = MagicMock()
        mock_token.user = MagicMock(username="testuser")
        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.first.return_value = mock_token
        monkeypatch.setattr("src.main_app.db.services.user_token_service.db.session.query", lambda cls: mock_query)

        result = UserTokenService().get_authenticated_user_token(1)

        assert result == mock_token

    def test_returns_none_when_token_is_none(self, monkeypatch):
        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.first.return_value = None
        monkeypatch.setattr("src.main_app.db.services.user_token_service.db.session.query", lambda cls: mock_query)

        result = UserTokenService().get_authenticated_user_token(1)

        assert result is None

    def test_returns_none_when_token_user_is_none(self, monkeypatch):
        mock_token = MagicMock()
        mock_token.user = None
        mock_query = MagicMock()
        mock_query.options.return_value.filter.return_value.first.return_value = mock_token
        monkeypatch.setattr("src.main_app.db.services.user_token_service.db.session.query", lambda cls: mock_query)

        result = UserTokenService().get_authenticated_user_token(1)

        assert result is None

    def test_handles_exception_gracefully(self, monkeypatch):
        mock_query = MagicMock()
        mock_query.options.side_effect = Exception("DB error")
        monkeypatch.setattr("src.main_app.db.services.user_token_service.db.session.query", lambda cls: mock_query)

        result = UserTokenService().get_authenticated_user_token(1)

        assert result is None


class TestGetUserToken:
    """Tests for get_user_token."""

    def test_returns_token_for_valid_user_id(self, monkeypatch):
        mock_token = MagicMock(spec=UserTokenRecord, user_id=1)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_token
        monkeypatch.setattr("src.main_app.db.services.user_token_service.db.session.query", lambda cls: mock_query)

        result = UserTokenService().get_user_token(1)

        assert result == mock_token

    def test_returns_token_for_valid_user_id_str(self, monkeypatch):
        mock_token = MagicMock(spec=UserTokenRecord, user_id=1)
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_token
        monkeypatch.setattr("src.main_app.db.services.user_token_service.db.session.query", lambda cls: mock_query)

        result = UserTokenService().get_user_token("1")

        assert result == mock_token

    def test_returns_none_for_none_user_id(self):
        result = UserTokenService().get_user_token(None)

        assert result is None

    def test_returns_none_for_zero_user_id(self):
        result = UserTokenService().get_user_token(0)

        assert result is None

    def test_returns_none_for_empty_string_user_id(self):
        result = UserTokenService().get_user_token("")

        assert result is None

    def test_returns_none_when_no_token_found(self, monkeypatch):
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        monkeypatch.setattr("src.main_app.db.services.user_token_service.db.session.query", lambda cls: mock_query)

        result = UserTokenService().get_user_token(999)

        assert result is None


class TestCreateUserToken:
    """Tests for create_user_token."""

    def test_creates_and_returns_record(self, monkeypatch):
        mock_db = MagicMock()
        monkeypatch.setattr("src.main_app.db.services.user_token_service.db", mock_db)
        monkeypatch.setattr(
            "src.main_app.db.services.user_token_service.encrypt_value",
            lambda x: b"enc_" + x.encode(),
        )

        result = UserTokenService().create_user_token(1, "key", "secret")

        assert result.user_id == 1
        assert result.access_token == b"enc_key"
        assert result.access_secret == b"enc_secret"
        mock_db.session.add.assert_called_once_with(result)
        mock_db.session.commit.assert_called_once()
        mock_db.session.refresh.assert_called_once_with(result)


class TestUpdateUserToken:
    """Tests for update_user_token."""

    def test_updates_existing_token(self, monkeypatch):
        mock_db = MagicMock()
        monkeypatch.setattr("src.main_app.db.services.user_token_service.db", mock_db)
        monkeypatch.setattr(
            "src.main_app.db.services.user_token_service.encrypt_value",
            lambda x: b"enc_" + x.encode(),
        )
        mock_record = MagicMock(spec=UserTokenRecord)
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_record

        result = UserTokenService().update_user_token(1, "new_key", "new_secret")

        assert result == mock_record
        assert result.access_token == b"enc_new_key"
        assert result.access_secret == b"enc_new_secret"
        mock_db.session.commit.assert_called_once()
        mock_db.session.refresh.assert_called_once_with(result)

    def test_returns_none_when_token_not_found(self, monkeypatch):
        mock_db = MagicMock()
        monkeypatch.setattr("src.main_app.db.services.user_token_service.db", mock_db)
        mock_db.session.query.return_value.filter.return_value.first.return_value = None

        result = UserTokenService().update_user_token(999, "key", "secret")

        assert result is None


class TestUpsertUserToken:
    """Tests for upsert_user_token."""

    def test_calls_create_when_no_existing_token(self, monkeypatch):
        mock_db = MagicMock()
        monkeypatch.setattr("src.main_app.db.services.user_token_service.db", mock_db)
        monkeypatch.setattr(
            "src.main_app.db.services.user_token_service.encrypt_value",
            lambda x: b"enc_" + x.encode(),
        )
        mock_db.session.query.return_value.filter.return_value.first.return_value = None

        result = UserTokenService().upsert_user_token(1, "key", "secret")

        assert result.user_id == 1
        assert result.access_token == b"enc_key"
        assert result.access_secret == b"enc_secret"

    def test_calls_update_when_token_exists(self, monkeypatch):
        mock_db = MagicMock()
        monkeypatch.setattr("src.main_app.db.services.user_token_service.db", mock_db)
        monkeypatch.setattr(
            "src.main_app.db.services.user_token_service.encrypt_value",
            lambda x: b"enc_" + x.encode(),
        )
        mock_record = MagicMock(spec=UserTokenRecord)
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_record

        result = UserTokenService().upsert_user_token(1, "new_key", "new_secret")

        assert result == mock_record
        assert result.access_token == b"enc_new_key"
        assert result.access_secret == b"enc_new_secret"