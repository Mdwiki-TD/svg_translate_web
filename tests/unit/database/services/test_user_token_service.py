"""
Integration tests for user_token_service module.
"""

from __future__ import annotations

from src.main_app.database.services.user_token_service import UserTokenService
from src.main_app.database.services.users_service import UsersService


class TestSetup:
    def setup_method(self):
        self.service = UserTokenService()
        self.user_service = UsersService()


class TestDeleteUserCascades(TestSetup):
    def test_delete_user_cascades(self) -> None:
        user = self.user_service.create_user("svc_dave")
        self.service.upsert_user_token(user_id=user.user_id, encrypted_token=b"k", encrypted_secret=b"s")
        assert self.service.get_record_by_id(user.user_id) is not None


class TestUpsertGetDeleteUserToken(TestSetup):
    def test_upsert_get_delete_user_token(self) -> None:
        # Test insert
        user = self.user_service.create_user("svc_eve")
        self.service.upsert_user_token(user_id=user.user_id, encrypted_token=b"key", encrypted_secret=b"secret")

        token_record = self.service.get_record_by_id(user.user_id)
        assert token_record is not None
        assert token_record.access_token is not None
        assert token_record.access_secret is not None

        # Test update
        self.service.upsert_user_token(user_id=user.user_id, encrypted_token=b"new_key", encrypted_secret=b"new_secret")
        token_record = self.service.get_record_by_id(user.user_id)

        # Test delete token only
        self.service.delete(user.user_id)
        assert self.service.get_record_by_id(user.user_id) is None


class TestGetAuthenticatedUserToken(TestSetup):
    """Tests for get_authenticated_user_token."""

    def test_returns_token_when_user_exists(self):
        """Test returns token when user exists and has user relationship loaded."""
        user = self.user_service.create_user("svc_eve")
        self.service.upsert_user_token(user_id=user.user_id, encrypted_token=b"key", encrypted_secret=b"secret")

        result = self.service.get_authenticated_user_token(user.user_id)

        assert result is not None

    def test_returns_none_when_token_is_none(self):
        """Test returns None when token query returns None."""
        result = self.service.get_authenticated_user_token(1)

        assert result is None

    def test_returns_none_when_token_user_is_none(self):
        """Test returns None when token.user is None."""
        result = self.service.get_authenticated_user_token(1)

        assert result is None

    def test_handles_exception_gracefully(self):
        """Test returns None when an exception is raised."""
        result = self.service.get_authenticated_user_token(1)

        assert result is None


class TestGetUserToken(TestSetup):
    """Tests for get_record_by_id."""

    def test_returns_token_for_valid_user_id(self):
        """Test returns token for a valid integer user_id."""
        user = self.user_service.create_user("svc_eve")
        self.service.upsert_user_token(user_id=user.user_id, encrypted_token=b"key", encrypted_secret=b"secret")
        result = self.service.get_record_by_id(user.user_id)

        assert result is not None

    def test_returns_token_for_valid_user_id_str(self):
        """Test returns token for a valid string user_id."""
        user = self.user_service.create_user("svc_eve")
        self.service.upsert_user_token(user_id=user.user_id, encrypted_token=b"key", encrypted_secret=b"secret")
        result = self.service.get_record_by_id(str(user.user_id))

        assert result is not None

    def test_returns_none_for_zero_user_id(self):
        """Test returns None when user_id is 0 (falsy check)."""
        result = self.service.get_record_by_id(0)

        assert result is None

    def test_returns_none_for_empty_string_user_id(self):
        """Test returns None when user_id is an empty string."""
        result = self.service.get_record_by_id("")

        assert result is None

    def test_returns_none_when_no_token_found(self):
        """Test returns None when no matching token record exists."""
        result = self.service.get_record_by_id(999)

        assert result is None


class TestCreateUserToken(TestSetup):
    """Tests for create."""

    def test_creates_and_returns_record(self):
        """Test creates a new UserTokenRecord and returns it."""
        user = self.user_service.create_user("svc_eve")
        result = self.service.create(user_id=user.user_id, access_token=b"key", access_secret=b"secret")
        assert result is not None
        assert result.user_id == user.user_id
        assert result.access_token == b"key"
        assert result.access_secret == b"secret"


class TestUpsertUserToken(TestSetup):
    """Tests for upsert_user_token."""

    def test_calls_create_when_no_existing_token(self):
        """Test calls create when no existing token is found."""
        user = self.user_service.create_user("testz")
        token = self.service.get_record_by_id(user.user_id)
        assert token is None

        result = self.service.upsert_user_token(user.user_id, b"enc_key", b"enc_secret")

        assert result is not None
        assert result.user_id == user.user_id
        assert result.access_token == b"enc_key"
        assert result.access_secret == b"enc_secret"
