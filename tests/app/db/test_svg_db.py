import pytest
from unittest.mock import MagicMock, patch
from src.app.config import DbConfig
from src.app.db.svg_db import (
    get_db, close_cached_db, execute_query, fetch_query,
    execute_query_safe, fetch_query_safe, _db
)
from src.app.db.db_class import Database


@pytest.fixture(autouse=True)
def cleanup_cached_db():
    close_cached_db()
    yield
    close_cached_db()


@patch("src.app.db.svg_db.Database")
@patch("src.app.db.svg_db.settings")
def test_get_db(mock_settings, mock_database_cls):
    mock_settings.database_data = DbConfig(**{"host": "localhost"})
    mock_db_instance = MagicMock(spec=Database)
    mock_database_cls.return_value = mock_db_instance

    # First call: should instantiate
    db1 = get_db()
    assert db1 is mock_db_instance
    mock_database_cls.assert_called_once_with({"host": "localhost"})

    # Second call: should return cached
    db2 = get_db()
    assert db2 is mock_db_instance
    mock_database_cls.assert_called_once()


@patch("src.app.db.svg_db.Database")
@patch("src.app.db.svg_db.settings")
def test_close_cached_db(mock_settings, mock_database_cls):
    mock_settings.database_data = DbConfig(**{"host": "localhost"})
    db = get_db()

    close_cached_db()
    db.close.assert_called_once()

    # Calling again should do nothing (no error)
    close_cached_db()


@patch("src.app.db.svg_db.get_db")
def test_execute_query(mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_db

    execute_query("SELECT 1", ("param",))
    mock_db.execute_query.assert_called_once_with("SELECT 1", ("param",))


@patch("src.app.db.svg_db.get_db")
def test_fetch_query(mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_db
    mock_db.fetch_query.return_value = [{"col": 1}]

    result = fetch_query("SELECT *", None)
    assert result == [{"col": 1}]
    mock_db.fetch_query.assert_called_once_with("SELECT *", None)


@patch("src.app.db.svg_db.get_db")
def test_execute_query_safe(mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_db

    execute_query_safe("UPDATE table", (1,))
    mock_db.execute_query_safe.assert_called_once_with("UPDATE table", (1,))


@patch("src.app.db.svg_db.get_db")
def test_fetch_query_safe(mock_get_db):
    mock_db = MagicMock()
    mock_get_db.return_value.__enter__.return_value = mock_db
    mock_db.fetch_query_safe.return_value = []

    result = fetch_query_safe("SELECT bad", None)
    assert result == []
    mock_db.fetch_query_safe.assert_called_once_with("SELECT bad", None)
