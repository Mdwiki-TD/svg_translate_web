# pyright: reportAttributeAccessIssue=false
"""
Tests for UserTokenService.

Part 1 (integration): every public method against the real test database.
Part 2 (unit): retry_on_db_disconnect behaviour on the decorated method
(get_authenticated_user_context), using a mocked session so no real
connection drop is needed.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pymysql
import pytest
from sqlalchemy.exc import OperationalError
from src.main_app.database import db
from src.main_app.database.models import AdminUserRecord
from src.main_app.database.services.users.user_token_service import UserTokenService
from src.main_app.database.services.users.users_service import UsersService


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def unique_name(prefix: str = "svc") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class TestSetup:
    def setup_method(self):
        self.service = UserTokenService()
        self.user_service = UsersService()

    def make_user(self, prefix: str = "svc"):
        user = self.user_service.create_user(unique_name(prefix))
        assert user is not None
        return user

    def make_user_with_token(self, token: bytes = b"key", secret: bytes = b"secret"):
        user = self.make_user()
        self.service.upsert_user_token(user.user_id, token, secret)
        return user

    @staticmethod
    def add_admin(username: str, is_active: bool = True) -> None:
        db.session.add(AdminUserRecord(username=username, is_active=is_active))
        db.session.commit()


# --------------------------------------------------------------------------- #
# Part 1: integration tests
# --------------------------------------------------------------------------- #
class TestUpsertUserToken(TestSetup):
    def test_creates_when_missing(self):
        user = self.make_user()
        assert self.service.get_record_by_id(user.user_id) is None

        result = self.service.upsert_user_token(user.user_id, b"enc_key", b"enc_secret")

        assert result is not None
        assert result.user_id == user.user_id
        assert result.access_token == b"enc_key"
        assert result.access_secret == b"enc_secret"

    def test_updates_when_existing(self):
        user = self.make_user_with_token(b"old_key", b"old_secret")

        result = self.service.upsert_user_token(user.user_id, b"new_key", b"new_secret")

        assert result.user_id == user.user_id
        assert result.access_token == b"new_key"
        assert result.access_secret == b"new_secret"

    def test_upsert_twice_keeps_single_row(self):
        user = self.make_user()
        self.service.upsert_user_token(user.user_id, b"k1", b"s1")
        self.service.upsert_user_token(user.user_id, b"k2", b"s2")

        count = self.service.session.query(self.service.model).filter_by(user_id=user.user_id).count()
        assert count == 1

    def test_update_persists(self):
        user = self.make_user_with_token(b"old", b"old")
        self.service.upsert_user_token(user.user_id, b"new", b"new")

        stored = self.service.get_record_by_id(user.user_id)
        assert stored is not None
        assert stored.access_token == b"new"
        assert stored.access_secret == b"new"


class TestGetRecordById(TestSetup):
    def test_returns_token_for_int_id(self):
        user = self.make_user_with_token()
        assert self.service.get_record_by_id(user.user_id) is not None

    def test_returns_token_for_str_id(self):
        user = self.make_user_with_token()
        assert self.service.get_record_by_id(str(user.user_id)) is not None

    def test_returns_none_for_zero(self):
        assert self.service.get_record_by_id(0) is None

    def test_returns_none_for_empty_string(self):
        assert self.service.get_record_by_id("") is None

    def test_returns_none_when_not_found(self):
        assert self.service.get_record_by_id(999_999_999) is None


class TestCreate(TestSetup):
    def test_creates_and_returns_record(self):
        user = self.make_user()

        result = self.service.create(user_id=user.user_id, access_token=b"key", access_secret=b"secret")

        assert result is not None
        assert result.user_id == user.user_id
        assert result.access_token == b"key"
        assert result.access_secret == b"secret"


class TestGetAuthenticatedUserToken(TestSetup):
    def test_returns_token_with_user_loaded(self):
        user = self.make_user_with_token()

        result = self.service.get_authenticated_user_token(user.user_id)

        assert result is not None
        assert result.user_id == user.user_id
        assert result.user is not None
        assert result.user.username == user.username

    def test_returns_none_when_no_token(self):
        user = self.make_user()  # user exists, token does not
        assert self.service.get_authenticated_user_token(user.user_id) is None

    def test_returns_none_for_unknown_user(self):
        assert self.service.get_authenticated_user_token(999_999_999) is None


class TestGetAuthenticatedUserContext(TestSetup):
    def test_returns_empty_context_when_no_token(self):
        user = self.make_user()  # user exists, token does not
        assert self.service.get_authenticated_user_context(user.user_id) == (
            None,
            False,
        )

    def test_returns_empty_context_for_unknown_user(self):
        assert self.service.get_authenticated_user_context(999_999_999) == (None, False)

    def test_empty_context_ignores_admin_without_token(self):
        """A user with an admin row but no token still gets no context."""
        user = self.make_user()
        self.add_admin(user.username)

        assert self.service.get_authenticated_user_context(user.user_id) == (
            None,
            False,
        )

    def test_plain_user_is_not_admin(self):
        user = self.make_user_with_token()

        token, is_admin = self.service.get_authenticated_user_context(user.user_id)

        assert token is not None
        assert token.user_id == user.user_id
        assert token.user.username == user.username
        assert is_admin is False

    def test_active_admin(self):
        user = self.make_user_with_token()
        self.add_admin(user.username, is_active=True)

        token, is_admin = self.service.get_authenticated_user_context(user.user_id)

        assert token is not None
        assert token.user_id == user.user_id
        assert is_admin is True

    def test_inactive_admin_is_not_admin(self):
        user = self.make_user_with_token()
        self.add_admin(user.username, is_active=False)

        _, is_admin = self.service.get_authenticated_user_context(user.user_id)

        assert is_admin is False

    def test_other_users_admin_does_not_leak(self):
        user = self.make_user_with_token()
        other = self.make_user_with_token()
        self.add_admin(other.username)

        _, is_admin = self.service.get_authenticated_user_context(user.user_id)

        assert is_admin is False

    def test_returns_python_bool(self):
        user = self.make_user_with_token()

        _, is_admin = self.service.get_authenticated_user_context(user.user_id)

        assert isinstance(is_admin, bool)


class TestGetUserTokenByUsername(TestSetup):
    def test_returns_token_for_username(self):
        user = self.make_user_with_token()

        result = self.service.get_user_token_by_username(user.username)

        assert result is not None
        assert result.user_id == user.user_id

    def test_returns_none_for_unknown_username(self):
        assert self.service.get_user_token_by_username(unique_name("missing")) is None

    def test_returns_none_when_user_has_no_token(self):
        user = self.make_user()
        assert self.service.get_user_token_by_username(user.username) is None


class TestUpdateLastUsed(TestSetup):
    def test_returns_none_when_no_token(self):
        assert self.service.update_last_used(999_999_999) is None

    def test_sets_last_used_at(self):
        user = self.make_user_with_token()
        before = datetime.utcnow().replace(microsecond=0)

        result = self.service.update_last_used(user.user_id)

        assert result is not None
        assert result.last_used_at is not None
        assert result.last_used_at >= before

    def test_does_not_change_credentials(self):
        user = self.make_user_with_token(b"keep_key", b"keep_secret")

        result = self.service.update_last_used(user.user_id)

        assert result is not None
        assert result.access_token == b"keep_key"
        assert result.access_secret == b"keep_secret"

    def test_persists(self):
        user = self.make_user_with_token()
        self.service.update_last_used(user.user_id)
        result = self.service.get_record_by_id(user.user_id)
        assert result is not None
        assert result.last_used_at is not None


class TestDeleteTokenByUserId(TestSetup):
    def test_returns_false_when_no_token(self):
        assert self.service.delete_token_by_user_id(999_999_999) is False

    def test_deletes_existing_token(self):
        user = self.make_user_with_token()

        assert self.service.delete_token_by_user_id(user.user_id) is True
        assert self.service.get_record_by_id(user.user_id) is None

    def test_second_delete_returns_false(self):
        user = self.make_user_with_token()
        self.service.delete_token_by_user_id(user.user_id)

        assert self.service.delete_token_by_user_id(user.user_id) is False

    def test_keeps_the_user(self):
        user = self.make_user_with_token()
        self.service.delete_token_by_user_id(user.user_id)

        assert self.user_service.get_record_by_id(user.user_id) is not None


# --------------------------------------------------------------------------- #
# Part 2: retry_on_db_disconnect on the decorated methods (mocked session)
# --------------------------------------------------------------------------- #
GONE_AWAY = (2006, "MySQL server has gone away (BrokenPipeError(32, 'Broken pipe'))")
LOST_CONN = (
    2013,
    "Lost connection to MySQL server during query ([SSL: RECORD_LAYER_FAILURE])",
)
ACCESS_DENIED = (1045, "Access denied for user")

MAX_RETRIES = 3  # DEFAULT_MAX_RETRIES of the decorator


def make_error(code_and_msg: tuple[int, str]) -> OperationalError:
    return OperationalError("SELECT 1", {}, pymysql.err.OperationalError(*code_and_msg))


def make_token(with_user: bool = True) -> MagicMock:
    token = MagicMock()
    token.user = MagicMock() if with_user else None
    return token


def make_session(side_effects: list) -> MagicMock:
    """
    Fake session: query() returns a fluent mock where join/options/filter
    return itself and first() yields `side_effects` one item per attempt.
    Works for both decorated methods regardless of their chain shape.
    """
    query = MagicMock()
    for name in ("join", "options", "filter"):
        getattr(query, name).return_value = query
    query.first.side_effect = side_effects

    session = MagicMock()
    session.query.return_value = query
    return session


@pytest.fixture
def retry_service(monkeypatch) -> UserTokenService:
    monkeypatch.setattr("time.sleep", lambda _s: None)  # no real backoff
    monkeypatch.setattr(db.session, "rollback", MagicMock())  # keep the shared session untouched
    return UserTokenService()


class TestGetAuthenticatedUserTokenUnit:
    """get_authenticated_user_token is a plain method (no retry decorator)."""

    def test_returns_token_when_user_loaded(self, retry_service):
        token = make_token()
        retry_service.session = make_session([token])

        assert retry_service.get_authenticated_user_token(8) is token

    def test_returns_none_when_token_missing(self, retry_service):
        retry_service.session = make_session([None])

        assert retry_service.get_authenticated_user_token(8) is None

    def test_returns_none_when_token_has_no_user(self, retry_service):
        retry_service.session = make_session([make_token(with_user=False)])

        assert retry_service.get_authenticated_user_token(8) is None

    def test_disconnect_is_not_retried(self, retry_service):
        retry_service.session = make_session([make_error(GONE_AWAY), make_token()])

        with pytest.raises(OperationalError):
            retry_service.get_authenticated_user_token(8)

        assert retry_service.session.query.call_count == 1
        db.session.rollback.assert_not_called()


class TestRetryEdgeCases:
    @pytest.mark.parametrize(("raw", "expected"), [(1, True), (0, False)], ids=["truthy", "falsy"])
    def test_context_coerces_flag_to_bool(self, retry_service, raw, expected):
        token = make_token()
        retry_service.session = make_session([(token, raw)])

        result = retry_service.get_authenticated_user_context(8)

        assert result == (token, expected)
        assert isinstance(result[1], bool)

    def test_undecorated_methods_are_not_retried(self, retry_service):
        """get_user_token_by_username has no retry; the error must surface at once."""
        retry_service.session = make_session([make_error(GONE_AWAY), make_token()])

        with pytest.raises(OperationalError):
            retry_service.get_user_token_by_username("x")

        assert retry_service.session.query.call_count == 1


def _context_success() -> tuple[Any, Any]:
    """(row returned by first(), expected return value of the service method)."""
    token = make_token()
    return (token, True), (token, True)


class TestRetryOnDisconnectContext:
    """
    Shared retry scenarios for any service method decorated with
    @retry_on_db_disconnect(). Not collected by pytest on its own (the name
    does not start with "Test"); each subclass sets:
    """

    def call(self, service: UserTokenService, *args: Any) -> Any:
        return service.get_authenticated_user_context(*args)

    def test_no_retry_on_success(self, retry_service):
        row, expected = _context_success()
        retry_service.session = make_session([row])

        assert self.call(retry_service, 8) == expected
        assert retry_service.session.query.call_count == 1
        db.session.rollback.assert_not_called()

    @pytest.mark.parametrize("error", [GONE_AWAY, LOST_CONN], ids=["2006", "2013"])
    def test_retries_then_succeeds(self, retry_service, error):
        row, expected = _context_success()
        retry_service.session = make_session([make_error(error), row])

        assert self.call(retry_service, 8) == expected
        assert retry_service.session.query.call_count == 2
        db.session.rollback.assert_called_once()

    def test_multiple_retries(self, retry_service):
        row, expected = _context_success()
        retry_service.session = make_session([make_error(GONE_AWAY), make_error(LOST_CONN), row])

        assert self.call(retry_service, 8) == expected
        assert retry_service.session.query.call_count == 3
        assert db.session.rollback.call_count == 2

    def test_raises_after_max_retries(self, retry_service):
        # 1 initial attempt + MAX_RETRIES retries, all failing
        retry_service.session = make_session([make_error(GONE_AWAY)] * (MAX_RETRIES + 1))

        with pytest.raises(OperationalError):
            self.call(retry_service, 8)

        assert retry_service.session.query.call_count == MAX_RETRIES + 1

    def test_non_disconnect_error_not_retried(self, retry_service):
        retry_service.session = make_session([make_error(ACCESS_DENIED)])

        with pytest.raises(OperationalError):
            self.call(retry_service, 8)

        assert retry_service.session.query.call_count == 1
        db.session.rollback.assert_not_called()

    def test_non_operational_error_not_retried(self, retry_service):
        retry_service.session = make_session([ValueError("boom")])

        with pytest.raises(ValueError):
            self.call(retry_service, 8)

        assert retry_service.session.query.call_count == 1

    def test_rollback_failure_does_not_stop_retry(self, retry_service, monkeypatch):
        monkeypatch.setattr(db.session, "rollback", MagicMock(side_effect=RuntimeError("dead")))
        row, expected = _context_success()
        retry_service.session = make_session([make_error(GONE_AWAY), row])

        assert self.call(retry_service, 8) == expected

    def test_none_result_after_retry(self, retry_service):
        retry_service.session = make_session([make_error(GONE_AWAY), None])

        assert self.call(retry_service, 8) == (None, False)
