from unittest.mock import MagicMock, patch

import pytest
from pymysql.cursors import DictCursor

from src.main_app.config import DbConfig
from src.main_app.db.db_class import Database, MaxUserConnectionsError


def test_MaxUserConnectionsError():
    """Test MaxUserConnectionsError exception."""
    # Test basic instantiation
    error = MaxUserConnectionsError()
    assert isinstance(error, Exception)
    assert str(error) == ""

    # Test with message
    error_with_msg = MaxUserConnectionsError("Too many connections")
    assert str(error_with_msg) == "Too many connections"


@patch("src.main_app.db.db_class.get_http_engine")
def test_Database_init_basic(mock_get_engine):
    """Test Database initialization with basic credentials."""
    database_config = DbConfig(db_name="testdb", db_host="localhost", db_user="testuser", db_password="testpass")

    db = Database(database_config)

    # Check that instance attributes are set correctly (for backward compatibility)
    assert db.host == "localhost"
    assert db.dbname == "testdb"
    assert db.user == "testuser"
    assert db.password == "testpass"
    assert db.credentials == {"user": "testuser", "password": "testpass"}
    assert db._lock is not None
    assert hasattr(db._lock, "acquire")
    assert db._use_bg_engine is False


@patch("src.main_app.db.db_class.get_http_engine")
def test_Database_init_with_bg_engine(mock_get_engine):
    """Test Database initialization with background engine flag."""
    database_config = DbConfig(db_name="testdb", db_host="localhost", db_user="testuser", db_password="testpass")

    db = Database(database_config, use_bg_engine=True)

    assert db._use_bg_engine is True


@patch("src.main_app.db.db_class.get_http_engine")
def test_Database_connect_is_noop(mock_get_engine):
    """Test Database _connect is a no-op with SQLAlchemy pooling."""
    database_config = DbConfig(db_name="testdb", db_host="localhost", db_user="testuser", db_password="testpass")

    db = Database(database_config)
    
    # _connect should be a no-op and not raise
    db._connect()
    db._ensure_connection()
    db.close()


@patch("src.main_app.db.db_class.get_http_engine")
def test_Database_context_manager(mock_get_engine):
    """Test Database as context manager."""
    database_config = DbConfig(db_name="testdb", db_host="localhost", db_user="testuser", db_password="testpass")

    # Use database as context manager - should work without errors
    with Database(database_config) as db:
        assert db is not None


@patch("src.main_app.db.db_class.get_http_engine")
def test_Database_use_bg_engine_gets_correct_engine(mock_get_http_engine):
    """Test that use_bg_engine=True uses get_bg_engine."""
    database_config = DbConfig(db_name="testdb", db_host="localhost", db_user="testuser", db_password="testpass")
    
    mock_bg_engine = MagicMock()
    with patch("src.main_app.db.db_class.get_bg_engine", return_value=mock_bg_engine) as mock_get_bg:
        db = Database(database_config, use_bg_engine=True)
        # Access engine to trigger lazy initialization
        engine = db._get_engine()
        mock_get_bg.assert_called_once()
        assert engine == mock_bg_engine


@patch("src.main_app.db.db_class.get_http_engine")
def test_Database_use_http_engine_by_default(mock_get_http_engine):
    """Test that use_bg_engine=False uses get_http_engine."""
    database_config = DbConfig(db_name="testdb", db_host="localhost", db_user="testuser", db_password="testpass")
    
    mock_http_engine = MagicMock()
    mock_get_http_engine.return_value = mock_http_engine
    
    db = Database(database_config, use_bg_engine=False)
    # Access engine to trigger lazy initialization
    engine = db._get_engine()
    mock_get_http_engine.assert_called_once()
    assert engine == mock_http_engine


def test_exception_code_with_pymysql_error():
    """Test _exception_code extracts code from PyMySQL errors."""
    database_config = DbConfig(db_name="testdb", db_host="localhost", db_user="testuser", db_password="testpass")
    db = Database(database_config)
    
    # Test with a mock PyMySQL error
    mock_error = MagicMock()
    mock_error.args = (1203, "max_user_connections")
    
    with patch.object(db, '_exception_code', return_value=1203):
        code = db._exception_code(mock_error)
        assert code == 1203


def test_should_retry_with_retryable_code():
    """Test _should_retry returns True for retryable error codes."""
    database_config = DbConfig(db_name="testdb", db_host="localhost", db_user="testuser", db_password="testpass")
    db = Database(database_config)
    
    # Test retryable codes
    for code in Database.RETRYABLE_ERROR_CODES:
        mock_error = MagicMock()
        mock_error.args = (code, "error message")
        with patch.object(db, '_exception_code', return_value=code):
            assert db._should_retry(mock_error) is True


def test_should_retry_with_non_retryable_code():
    """Test _should_retry returns False for non-retryable error codes."""
    database_config = DbConfig(db_name="testdb", db_host="localhost", db_user="testuser", db_password="testpass")
    db = Database(database_config)
    
    # Test non-retryable code
    mock_error = MagicMock()
    mock_error.args = (999, "error message")
    with patch.object(db, '_exception_code', return_value=999):
        assert db._should_retry(mock_error) is False


def test_compute_backoff():
    """Test _compute_backoff increases with attempt number."""
    database_config = DbConfig(db_name="testdb", db_host="localhost", db_user="testuser", db_password="testpass")
    db = Database(database_config)
    
    backoff1 = db._compute_backoff(1)
    backoff2 = db._compute_backoff(2)
    backoff3 = db._compute_backoff(3)
    
    # Backoff should increase exponentially
    assert backoff2 > backoff1
    assert backoff3 > backoff2
    
    # Base backoff is 0.2, so:
    # attempt 1: 0.2 * 2^0 = 0.2
    # attempt 2: 0.2 * 2^1 = 0.4
    # attempt 3: 0.2 * 2^2 = 0.8
    assert 0.1 <= backoff1 <= 0.4
    assert 0.3 <= backoff2 <= 0.6
    assert 0.7 <= backoff3 <= 1.0
