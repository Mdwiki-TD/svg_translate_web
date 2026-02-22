import pytest
from unittest.mock import MagicMock, call
import pymysql
from src.app.db.db_CoordinatorsDB import CoordinatorsDB, CoordinatorRecord

@pytest.fixture
def mock_db_class(mocker):
    return mocker.patch("src.app.db.db_CoordinatorsDB.Database")

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
        "INSERT INTO admin_users (username, is_active) VALUES (%s, 1)",
        ("new_admin",)
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
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 10, "username": "newuser", "is_active": 1}
    ]
    
    record = coordinators_db.add("newuser")
    
    mock_db_instance.execute_query.assert_called_with(
        "INSERT INTO admin_users (username, is_active) VALUES (%s, 1)",
        ("newuser",)
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
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 1, "username": "u", "is_active": 0}
    ]
    
    coordinators_db.set_active(1, True)
    
    mock_db_instance.execute_query_safe.assert_called_with(
        "UPDATE admin_users SET is_active = %s WHERE id = %s",
        (1, 1)
    )

def test_delete(coordinators_db, mock_db_instance):
    mock_db_instance.fetch_query_safe.return_value = [
        {"id": 1, "username": "u", "is_active": 1}
    ]

    record = coordinators_db.delete(1)

    mock_db_instance.execute_query_safe.assert_called_with(
        "DELETE FROM admin_users WHERE id = %s",
        (1,)
    )
    assert record.id == 1