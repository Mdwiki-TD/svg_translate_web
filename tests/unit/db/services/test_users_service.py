"""
Tests for src/main_app/db/services/users_service.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.db.exceptions import UserNotFoundError
from src.main_app.db.models import UserRecord
from src.main_app.db.services import users_service
from src.main_app.extensions import db

# ── Helpers ──────────────────────────────────────────────────────────


@pytest.fixture
def user_record() -> UserRecord:
    """Insert and return a fresh UserRecord in the real test DB."""
    record = UserRecord(username="test_user")
    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


# ── list_users ───────────────────────────────────────────────────────


class TestListUsers:
    """Tests for list_users()."""

    def test_returns_all_users(self, user_record: UserRecord) -> None:
        """Verify list_users returns all records from the users table."""
        result = users_service.list_users()
        assert len(result) == 1
        assert result[0].user_id == user_record.user_id
        assert result[0].username == "test_user"

    def test_returns_empty_when_no_users(self) -> None:
        """Verify list_users returns an empty list when no users exist."""
        assert users_service.list_users() == []


# ── get_user ─────────────────────────────────────────────────────────


class TestGetUser:
    """Tests for get_user()."""

    def test_returns_user_by_valid_id(self, user_record: UserRecord) -> None:
        """Verify get_user returns the correct user for a valid id."""
        result = users_service.get_user(user_record.user_id)
        assert result is not None
        assert result.user_id == user_record.user_id
        assert result.username == "test_user"

    def test_returns_none_for_zero_id(self) -> None:
        """Verify get_user returns None when user_id is 0."""
        assert users_service.get_user(0) is None

    def test_returns_none_for_none_id(self) -> None:
        """Verify get_user returns None when user_id is None."""
        assert users_service.get_user(None) is None  # type: ignore[arg-type]

    def test_returns_none_for_non_existent_id(self) -> None:
        """Verify get_user returns None when user_id does not exist."""
        assert users_service.get_user(999) is None


# ── get_user_by_username ─────────────────────────────────────────────


class TestGetUserByUsername:
    """Tests for get_user_by_username()."""

    def test_returns_user_by_existing_username(self, user_record: UserRecord) -> None:
        """Verify get_user_by_username returns the correct user."""
        result = users_service.get_user_by_username("test_user")
        assert result is not None
        assert result.user_id == user_record.user_id
        assert result.username == "test_user"

    def test_returns_none_for_empty_username(self) -> None:
        """Verify get_user_by_username returns None for empty or whitespace-only strings."""
        assert users_service.get_user_by_username("") is None
        assert users_service.get_user_by_username("  ") is None

    def test_returns_none_for_none_username(self) -> None:
        """Verify get_user_by_username returns None when username is None."""
        assert users_service.get_user_by_username(None) is None  # type: ignore[arg-type]

    def test_returns_none_for_non_existent_username(self) -> None:
        """Verify get_user_by_username returns None for a non-existent username."""
        assert users_service.get_user_by_username("nonexistent") is None


# ── create_user ──────────────────────────────────────────────────────


class TestCreateUser:
    """Tests for create_user()."""

    def test_creates_new_user(self) -> None:
        """Verify create_user inserts a new row and returns it."""
        result = users_service.create_user("new_user")
        assert result.username == "new_user"
        assert result.user_id is not None

        persisted = db.session.query(UserRecord).filter_by(username="new_user").first()
        assert persisted is not None
        assert persisted.user_id == result.user_id

    def test_returns_existing_user(self, user_record: UserRecord) -> None:
        """Verify create_user is idempotent — returns existing row when username already exists."""
        result = users_service.create_user("test_user")
        assert result.user_id == user_record.user_id
        assert result.username == "test_user"

    def test_race_condition_returns_existing(self) -> None:
        """Verify create_user recovers when commit fails and a concurrent insert created the user.

        Simulates: first query → None, commit → exception, rollback, second query → existing.
        """
        existing_user = MagicMock(spec=UserRecord)
        existing_user.username = "race_user"

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.side_effect = [None, existing_user]
        mock_query.filter.return_value = mock_filter
        mock_db.session.query.return_value = mock_query
        mock_db.session.commit.side_effect = Exception("race")

        with patch("src.main_app.db.services.users_service.db", mock_db):
            result = users_service.create_user("race_user")

        assert result is existing_user
        mock_db.session.add.assert_called_once()
        mock_db.session.rollback.assert_called_once()

    def test_race_condition_raises(self) -> None:
        """Verify create_user re-raises when commit fails and no concurrent insert occurred."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.side_effect = [None, None]
        mock_query.filter.return_value = mock_filter
        mock_db.session.query.return_value = mock_query
        mock_db.session.commit.side_effect = Exception("db error")

        with patch("src.main_app.db.services.users_service.db", mock_db):
            with pytest.raises(Exception, match="db error"):
                users_service.create_user("fail_user")

        mock_db.session.add.assert_called_once()
        mock_db.session.rollback.assert_called_once()


# ── toggle_can_run_jobs ──────────────────────────────────────────────


class TestToggleCanRunJobs:
    """Tests for toggle_can_run_jobs()."""

    def test_toggles_to_true(self, user_record: UserRecord) -> None:
        """Verify toggle_can_run_jobs sets can_run_jobs to True."""
        result = users_service.toggle_can_run_jobs(user_record.user_id, True)
        assert bool(result.can_run_jobs) is True

        refreshed = db.session.get(UserRecord, user_record.user_id)
        assert refreshed is not None
        assert bool(refreshed.can_run_jobs) is True

    def test_toggles_to_false(self, user_record: UserRecord) -> None:
        """Verify toggle_can_run_jobs sets can_run_jobs to False."""
        result = users_service.toggle_can_run_jobs(user_record.user_id, False)
        assert bool(result.can_run_jobs) is False

        refreshed = db.session.get(UserRecord, user_record.user_id)
        assert refreshed is not None
        assert bool(refreshed.can_run_jobs) is False

    def test_raises_for_missing_user(self) -> None:
        """Verify toggle_can_run_jobs raises UserNotFoundError for non-existent user_id."""
        with pytest.raises(UserNotFoundError, match="User record not found"):
            users_service.toggle_can_run_jobs(999, True)


# ── toggle_can_run_bg_jobs ───────────────────────────────────────────


class TestToggleCanRunBgJobs:
    """Tests for toggle_can_run_bg_jobs()."""

    def test_toggles_to_true(self, user_record: UserRecord) -> None:
        """Verify toggle_can_run_bg_jobs sets can_run_bg_jobs to True."""
        result = users_service.toggle_can_run_bg_jobs(user_record.user_id, True)
        assert bool(result.can_run_bg_jobs) is True

        refreshed = db.session.get(UserRecord, user_record.user_id)
        assert refreshed is not None
        assert bool(refreshed.can_run_bg_jobs) is True

    def test_toggles_to_false(self, user_record: UserRecord) -> None:
        """Verify toggle_can_run_bg_jobs sets can_run_bg_jobs to False."""
        result = users_service.toggle_can_run_bg_jobs(user_record.user_id, False)
        assert bool(result.can_run_bg_jobs) is False

        refreshed = db.session.get(UserRecord, user_record.user_id)
        assert refreshed is not None
        assert bool(refreshed.can_run_bg_jobs) is False

    def test_raises_for_missing_user(self) -> None:
        """Verify toggle_can_run_bg_jobs raises UserNotFoundError for non-existent user_id."""
        with pytest.raises(UserNotFoundError, match="User record not found"):
            users_service.toggle_can_run_bg_jobs(999, True)
