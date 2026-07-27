"""Tests for user_token_service module."""

from __future__ import annotations

import pytest

from src.main_app.db.services.user_token_service import UserTokenService
from src.main_app.db.services.users_service import UsersService

class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.user_service = UsersService()
        self.usertoken_service = UserTokenService()
        self.usertoken_service.encrypt_value = lambda value: b"enc_" + value.encode()

        self.user_record = self.user_service.create_user("token_user")
        self.user_token_record = self.usertoken_service.create_user_token(self.user_record.user_id, "key", "secret")


class TestDelete(TestSetup):
    def test_upsert_get_delete_user_token(self) -> None:
        self.usertoken_service.upsert_user_token(user_id=self.user_record.user_id, access_key="key", access_secret="secret")

        token_record = self.usertoken_service.get_user_token(self.user_record.user_id)
        assert token_record is not None
        assert token_record.access_token == b"enc_key"
        assert token_record.access_secret == b"enc_secret"

        self.usertoken_service.upsert_user_token(
            user_id=self.user_record.user_id, access_key="new_key", access_secret="new_secret"
        )
        token_record = self.usertoken_service.get_user_token(self.user_record.user_id)
        assert token_record is not None
        assert token_record.access_token == b"enc_new_key"
        assert token_record.access_secret == b"enc_new_secret"

        self.usertoken_service.delete(self.user_record.user_id)
        assert self.usertoken_service.get_user_token(self.user_record.user_id) is None

class TestGetAuthenticatedUserToken(TestSetup):
    """Tests for get_authenticated_user_token."""

    def test_returns_token_when_user_exists(self) -> None:
        """Test returns token when user exists and has user relationship loaded."""

        result = self.usertoken_service.get_authenticated_user_token(self.user_token_record.user_id)

        assert result is not None
        assert result.user_id == self.user_token_record.user_id
        assert result.user.username == "token_user"

    def test_returns_none_when_token_is_none(self) -> None:
        """Test returns None when token query returns None."""
        result = self.usertoken_service.get_authenticated_user_token(999)

        assert result is None


class TestGetUserToken(TestSetup):
    """Tests for get_user_token."""

    def test_returns_token_for_valid_user_id(self) -> None:
        """Test returns token for a valid integer user_id."""
        result = self.usertoken_service.get_user_token(self.user_token_record.user_id)

        assert result is not None
        assert result.user_id == self.user_token_record.user_id

    def test_returns_token_for_valid_user_id_str(self) -> None:
        """Test returns token for a valid string user_id."""
        result = self.usertoken_service.get_user_token(str(self.user_token_record.user_id))

        assert result is not None
        assert result.user_id == self.user_token_record.user_id

    def test_returns_none_for_none_user_id(self) -> None:
        """Test returns None when user_id is None."""
        result = self.usertoken_service.get_user_token(None)

        assert result is None

    def test_returns_none_for_zero_user_id(self) -> None:
        """Test returns None when user_id is 0 (falsy check)."""
        result = self.usertoken_service.get_user_token(0)

        assert result is None

    def test_returns_none_for_empty_string_user_id(self) -> None:
        """Test returns None when user_id is an empty string."""
        result = self.usertoken_service.get_user_token("")

        assert result is None

    def test_returns_none_when_no_token_found(self) -> None:
        """Test returns None when no matching token record exists."""
        result = self.usertoken_service.get_user_token(999)

        assert result is None


class TestCreateUserToken(TestSetup):
    """Tests for create_user_token."""

    def test_creates_and_returns_record(self) -> None:
        """Test creates a new UserTokenRecord and returns it."""
        user_record = self.user_service.create_user("token_user1")
        result = self.usertoken_service.create_user_token(user_record.user_id, "key", "secret")

        assert result.user_id == user_record.user_id
        assert result.access_token == b"enc_key"
        assert result.access_secret == b"enc_secret"

        persisted = self.usertoken_service.get(user_record.user_id)
        assert persisted is not None
        assert persisted.access_token == b"enc_key"
        assert persisted.access_secret == b"enc_secret"


    def test_upserts_and_returns_record(self) -> None:
        result = self.usertoken_service.upsert_user_token(self.user_record.user_id, "key", "secret")

        assert result.user_id == self.user_record.user_id
        assert result.access_token == b"enc_key"
        assert result.access_secret == b"enc_secret"

        persisted = self.usertoken_service.get(self.user_record.user_id)
        assert persisted is not None
        assert persisted.access_token == b"enc_key"
        assert persisted.access_secret == b"enc_secret"

class TestUpdateUserToken(TestSetup):
    """Tests for update_user_token."""

    def test_updates_existing_token(self) -> None:
        """Test updates fields on an existing token record."""
        result = self.usertoken_service.update_user_token(self.user_token_record.user_id, "new_key", "new_secret")

        assert result is not None
        assert result.user_id == self.user_token_record.user_id
        assert result.access_token == b"enc_new_key"
        assert result.access_secret == b"enc_new_secret"

        persisted = self.usertoken_service.get(self.user_token_record.user_id)
        assert persisted is not None
        assert persisted.access_token == b"enc_new_key"
        assert persisted.access_secret == b"enc_new_secret"

    def test_returns_none_when_token_not_found(self) -> None:
        """Test returns None when no token record exists for the user."""
        result = self.usertoken_service.update_user_token(999, "key", "secret")

        assert result is None


class TestUpsertUserToken(TestSetup):
    """Tests for upsert_user_token."""

    def test_calls_create_when_no_existing_token(self) -> None:
        """Test creates a token when no existing token is found."""
        result = self.usertoken_service.upsert_user_token(self.user_record.user_id, "key", "secret")

        assert result.user_id == self.user_record.user_id
        assert result.access_token == b"enc_key"
        assert result.access_secret == b"enc_secret"
        assert self.usertoken_service.get(self.user_record.user_id) is not None

    def test_calls_update_when_token_exists(self) -> None:
        """Test updates the row when an existing token is found."""
        result = self.usertoken_service.upsert_user_token(self.user_token_record.user_id, "new_key", "new_secret")

        assert result.user_id == self.user_token_record.user_id
        assert result.access_token == b"enc_new_key"
        assert result.access_secret == b"enc_new_secret"
