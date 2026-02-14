import pytest
from unittest.mock import patch, MagicMock, Mock
import threading
import pymysql
from src.app.db.db_class import MaxUserConnectionsError, Database


def test_MaxUserConnectionsError():
    """Test MaxUserConnectionsError exception."""
    # Test basic instantiation
    error = MaxUserConnectionsError()
    assert isinstance(error, Exception)
    assert str(error) == ""

    # Test with message
    error_with_msg = MaxUserConnectionsError("Too many connections")
    assert str(error_with_msg) == "Too many connections"


@patch('src.app.db.db_class.pymysql')
def test_Database_init_basic(mock_pymysql):
    """Test Database initialization with basic credentials."""
    db_data = {
        "host": "localhost",
        "dbname": "testdb",
        "user": "testuser",
        "password": "testpass"
    }

    db = Database(db_data)

    # Check that instance attributes are set correctly
    assert db.host == "localhost"
    assert db.dbname == "testdb"
    assert db.user == "testuser"
    assert db.password == "testpass"
    assert db.credentials == {"user": "testuser", "password": "testpass"}
    assert db._lock is not None
    assert hasattr(db._lock, 'acquire')
    assert db.connection is None


@patch('src.app.db.db_class.pymysql')
def test_Database_init_with_connect_file(mock_pymysql):
    """Test Database initialization with connect file."""
    db_data = {
        "host": "localhost",
        "dbname": "testdb",
        "user": "testuser",
        "password": "testpass",
        "db_connect_file": "/path/to/config"
    }

    db = Database(db_data)

    # Check that instance attributes are set correctly
    assert db.credentials == {"read_default_file": "/path/to/config"}


@patch('src.app.db.db_class.pymysql')
def test_Database_connect(mock_pymysql):
    """Test Database _connect method."""
    db_data = {
        "host": "localhost",
        "dbname": "testdb",
        "user": "testuser",
        "password": "testpass"
    }

    db = Database(db_data)

    # Mock the pymysql.connect to return a mock connection
    mock_connection = MagicMock()
    mock_pymysql.connect.return_value = mock_connection

    # Call _connect
    db._connect()

    # Import the actual DictCursor class used by the module
    from pymysql.cursors import DictCursor

    # Verify pymysql.connect was called with correct parameters
    mock_pymysql.connect.assert_called_once_with(
        host="localhost",
        database="testdb",
        connect_timeout=5,
        read_timeout=10,
        write_timeout=10,
        charset="utf8mb4",
        init_command="SET time_zone = '+00:00'",
        autocommit=True,
        cursorclass=DictCursor,
        user="testuser",
        password="testpass"
    )

    # Verify that the connection was stored
    assert db.connection == mock_connection


@patch('src.app.db.db_class.pymysql')
def test_Database_ensure_connection_new(mock_pymysql):
    """Test Database _ensure_connection when no connection exists."""
    db_data = {
        "host": "localhost",
        "dbname": "testdb",
        "user": "testuser",
        "password": "testpass"
    }

    db = Database(db_data)

    # Mock the _connect method
    with patch.object(db, '_connect') as mock_connect:
        db._ensure_connection()

        # Verify _connect was called
        mock_connect.assert_called_once()


@patch('src.app.db.db_class.pymysql')
def test_Database_ensure_connection_ping(mock_pymysql):
    """Test Database _ensure_connection when connection exists."""
    db_data = {
        "host": "localhost",
        "dbname": "testdb",
        "user": "testuser",
        "password": "testpass"
    }

    db = Database(db_data)

    # Mock an existing connection
    mock_connection = MagicMock()
    db.connection = mock_connection

    # Call _ensure_connection
    db._ensure_connection()

    # Verify ping was called
    mock_connection.ping.assert_called_once_with(reconnect=True)


@patch('src.app.db.db_class.pymysql')
def test_Database_close(mock_pymysql):
    """Test Database close method."""
    db_data = {
        "host": "localhost",
        "dbname": "testdb",
        "user": "testuser",
        "password": "testpass"
    }

    db = Database(db_data)

    # Mock a connection
    mock_connection = MagicMock()
    db.connection = mock_connection

    # Call close
    db.close()

    # Verify connection was closed
    mock_connection.close.assert_called_once()
    assert db.connection is None


@patch('src.app.db.db_class.pymysql')
def test_Database_context_manager(mock_pymysql):
    """Test Database as context manager."""
    db_data = {
        "host": "localhost",
        "dbname": "testdb",
        "user": "testuser",
        "password": "testpass"
    }

    mock_connection = MagicMock()
    mock_pymysql.connect.return_value = mock_connection

    # Use database as context manager
    with Database(db_data) as db:
        # Trigger connection
        db._ensure_connection()
        # Verify connection was established
        assert db.connection is not None

    # Verify connection was closed after context
    mock_connection.close.assert_called_once()


@patch('src.app.db.db_class.pymysql')
def test_Database_execute_query_success(mock_pymysql):
    """Test Database execute_query method with success."""
    db_data = {
        "host": "localhost",
        "dbname": "testdb",
        "user": "testuser",
        "password": "testpass"
    }

    db = Database(db_data)

    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    mock_pymysql.connect.return_value = mock_connection
    db.connection = mock_connection

    # Mock cursor results
    mock_cursor.fetchall.return_value = [{"id": 1, "name": "test"}]

    # Execute a query
    result = db.execute_query("SELECT * FROM test", ())

    # Verify the query was executed
    mock_cursor.execute.assert_called_once_with("SELECT * FROM test", ())
    assert result == [{"id": 1, "name": "test"}]


@patch('src.app.db.db_class.pymysql')
def test_Database_fetch_query_success(mock_pymysql):
    """Test Database fetch_query method with success."""
    db_data = {
        "host": "localhost",
        "dbname": "testdb",
        "user": "testuser",
        "password": "testpass"
    }

    db = Database(db_data)

    # Mock the connection and cursor
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.cursor.return_value = mock_cursor
    mock_pymysql.connect.return_value = mock_connection
    db.connection = mock_connection

    # Mock cursor results
    mock_cursor.fetchall.return_value = [{"id": 1, "name": "test"}]

    # Execute a query
    result = db.fetch_query("SELECT * FROM test", ())

    # Verify the query was executed
    mock_cursor.execute.assert_called_once_with("SELECT * FROM test", ())
    assert result == [{"id": 1, "name": "test"}]