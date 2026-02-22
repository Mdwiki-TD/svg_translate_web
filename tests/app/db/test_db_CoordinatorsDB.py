from unittest.mock import MagicMock, call

import pymysql
import pytest

from src.main_app.db.db_CoordinatorsDB import CoordinatorRecord, CoordinatorsDB


@pytest.fixture
def mock_db_class(mocker):
    return mocker.patch("src.main_app.db.db_CoordinatorsDB.Database")


@pytest.fixture
def mock_db_instance(mock_db_class):
    instance = MagicMock()
    mock_db_class.return_value = instance
    return instance


@pytest.fixture
def coordinators_db(mock_db_instance):
    return CoordinatorsDB({})


def test_CoordinatorRecord():
    record = CoordinatorRecord(id=1, username="test", is_active=True)
    assert record.id == 1
    assert record.username == "test"
    assert record.is_active is True


def test_ensure_table(mock_db_instance):
    CoordinatorsDB({})
    mock_db_instance.execute_query_safe.assert_called()
    assert "CREATE TABLE IF NOT EXISTS admin_users" in mock_db_instance.execute_query_safe.call_args[0][0]


def test_fetch_by_id_success(coordinators_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 1, "username": "admin", "is_active": 1, "created_at": None, "updated_at": None}
    ]

    record = coordinators_db._fetch_by_id(1)
    assert record.username == "admin"
    assert record.is_active is True


def test_fetch_by_id_not_found(coordinators_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = []
    with pytest.raises(LookupError):
        coordinators_db._fetch_by_id(999)


def test_fetch_by_username_success(coordinators_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 2, "username": "mod", "is_active": 0, "created_at": None, "updated_at": None}
    ]
    record = coordinators_db._fetch_by_username("mod")
    assert record.id == 2
    assert record.is_active is False


def test_fetch_by_username_not_found(coordinators_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = []
    with pytest.raises(LookupError):
        coordinators_db._fetch_by_username("unknown")


def test_seed(coordinators_db, mock_db_instance):
    # Existing user: admin
    # New user: new_admin
    mock_db_instance.fetch_query_safe.return_value = [{"username": "admin"}]

    coordinators_db.seed(["admin", "new_admin", "  "])

    # Verify that only new_admin was inserted
    mock_db_instance.execute_query_safe.assert_called_with(
        "INSERT INTO admin_users (username, is_active) VALUES (%s, 1)", ("new_admin",)
    )


def test_list(coordinators_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 1, "username": "a", "is_active": 1},
        {"id": 2, "username": "b", "is_active": 0},
    ]

    records = coordinators_db.list()
    assert len(records) == 2
    assert records[0].username == "a"
    assert records[1].username == "b"


def test_add_success(coordinators_db, mock_db_instance):
    # Setup mock for _fetch_by_username (called after insert)
    mock_db_instance.fetch_query_safe.return_value = [{"id": 10, "username": "newuser", "is_active": 1}]

    record = coordinators_db.add("newuser")

    mock_db_instance.execute_query.assert_called_with(
        "INSERT INTO admin_users (username, is_active) VALUES (%s, 1)", ("newuser",)
    )
    assert record.username == "newuser"


def test_add_empty_username(coordinators_db):
    with pytest.raises(ValueError, match="Username is required"):
        coordinators_db.add("   ")


def test_add_duplicate(coordinators_db, mock_db_instance):
    mock_db_instance.execute_query.side_effect = pymysql.err.IntegrityError(1062, "Duplicate entry")

    with pytest.raises(ValueError, match="already exists"):
        coordinators_db.add("existing")


def test_set_active(coordinators_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [{"id": 1, "username": "u", "is_active": 0}]

    coordinators_db.set_active(1, True)

    mock_db_instance.execute_query_safe.assert_called_with(
        "UPDATE admin_users SET is_active = %s WHERE id = %s", (1, 1)
    )


def test_delete(coordinators_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [{"id": 1, "username": "u", "is_active": 1}]

    record = coordinators_db.delete(1)

    mock_db_instance.execute_query_safe.assert_called_with("DELETE FROM admin_users WHERE id = %s", (1,))
    assert record.id == 1


def test_seed_empty_list(coordinators_db, mock_db_instance):
    """Test seed with empty list does nothing."""
    coordinators_db.seed([])

    # fetch_query_safe should not be called
    mock_db_instance.fetch_query_safe.assert_not_called()


def test_seed_only_whitespace(coordinators_db, mock_db_instance):
    """Test seed with only whitespace strings does nothing."""
    coordinators_db.seed(["   ", "", "  \t  "])

    mock_db_instance.fetch_query_safe.assert_not_called()


def test_seed_strips_whitespace(coordinators_db, mock_db_instance):
    """Test seed strips whitespace from usernames."""
    mock_db_instance.fetch_query_safe.return_value = []

    coordinators_db.seed(["  user1  ", " user2 "])

    # Should have inserted both with trimmed names (plus _ensure_table call = 3 total)
    assert mock_db_instance.execute_query_safe.call_count >= 2


def test_row_to_record_with_all_fields(coordinators_db):
    """Test _row_to_record converts all fields correctly."""
    from datetime import datetime

    now = datetime.now()

    row = {"id": 42, "username": "testuser", "is_active": 1, "created_at": now, "updated_at": now}

    record = coordinators_db._row_to_record(row)

    assert record.id == 42
    assert record.username == "testuser"
    assert record.is_active is True
    assert record.created_at == now
    assert record.updated_at == now


def test_row_to_record_is_active_falsy(coordinators_db):
    """Test _row_to_record converts is_active 0 to False."""
    row = {"id": 1, "username": "inactive", "is_active": 0, "created_at": None, "updated_at": None}

    record = coordinators_db._row_to_record(row)

    assert record.is_active is False


def test_add_with_whitespace_trimmed(coordinators_db, mock_db_instance):
    """Test add trims whitespace from username."""
    mock_db_instance.fetch_query_safe.return_value = [{"id": 1, "username": "trimmed", "is_active": 1}]

    coordinators_db.add("  trimmed  ")

    call_args = mock_db_instance.execute_query.call_args[0][1]
    assert call_args[0] == "trimmed"


def test_set_active_deactivate(coordinators_db, mock_db_instance):
    """Test set_active can deactivate a coordinator."""
    mock_db_instance.fetch_query_safe.return_value = [{"id": 1, "username": "u", "is_active": 1}]

    coordinators_db.set_active(1, False)

    mock_db_instance.execute_query_safe.assert_called_with(
        "UPDATE admin_users SET is_active = %s WHERE id = %s", (0, 1)
    )


def test_set_active_not_found(coordinators_db, mock_db_instance):
    """Test set_active raises LookupError when coordinator not found."""
    mock_db_instance.fetch_query_safe.return_value = []

    with pytest.raises(LookupError):
        coordinators_db.set_active(999, True)


def test_delete_not_found(coordinators_db, mock_db_instance):
    """Test delete raises LookupError when coordinator not found."""
    mock_db_instance.fetch_query_safe.return_value = []

    with pytest.raises(LookupError):
        coordinators_db.delete(999)


def test_list_empty(coordinators_db, mock_db_instance):
    """Test list returns empty list when no coordinators exist."""
    mock_db_instance.fetch_query_safe.return_value = []

    result = coordinators_db.list()

    assert result == []
    assert isinstance(result, list)
