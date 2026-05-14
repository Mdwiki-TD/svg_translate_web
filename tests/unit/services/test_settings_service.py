from unittest.mock import MagicMock, patch

from src.main_app.db.services.settings_service import (
    _serialize_value,
)


@patch("src.main_app.db.db_Settings.Database")
def test_serialize_value_none(mock_database_class):
    """Test _serialize_value handles None."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    result = _serialize_value(None, "string")

    assert result is None


@patch("src.main_app.db.db_Settings.Database")
def test_serialize_value_boolean(mock_database_class):
    """Test _serialize_value handles booleans."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    assert _serialize_value(True, "boolean") == "true"
    assert _serialize_value(False, "boolean") == "false"


@patch("src.main_app.db.db_Settings.Database")
def test_serialize_value_integer(mock_database_class):
    """Test _serialize_value handles integers."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    assert _serialize_value(42, "integer") == "42"
    assert _serialize_value(-10, "integer") == "-10"


@patch("src.main_app.db.db_Settings.Database")
def test_serialize_value_json(mock_database_class):
    """Test _serialize_value handles JSON."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    assert _serialize_value({"key": "value"}, "json") == '{"key": "value"}'
    assert _serialize_value([1, 2, 3], "json") == "[1, 2, 3]"


@patch("src.main_app.db.db_Settings.Database")
def test_serialize_value_string(mock_database_class):
    """Test _serialize_value handles strings."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    assert _serialize_value("hello", "string") == "hello"
    assert _serialize_value(123, "string") == "123"
