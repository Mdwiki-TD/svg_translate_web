"""Tests for SettingsDB database operations."""

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.config import DbConfig
from src.main_app.db.db_Settings import SettingsDB


@pytest.fixture
def mock_db():
    """Create a mock database for testing."""
    mock = MagicMock()
    return mock


@pytest.fixture
def db_config():
    """Create a test database configuration."""
    return DbConfig(
        db_name="testdb",
        db_host="localhost",
        db_user="testuser",
        db_password="testpass",
    )


@patch("src.main_app.db.db_Settings.Database")
def test_settings_db_init(mock_database_class, db_config):
    """Test SettingsDB initialization creates table."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)

    mock_database_class.assert_called_once_with(db_config, use_bg_engine=False)
    mock_db.execute_query_safe.assert_called_once()
    # Verify the CREATE TABLE statement was executed
    call_args = mock_db.execute_query_safe.call_args[0][0]
    assert "CREATE TABLE IF NOT EXISTS `settings`" in call_args


@patch("src.main_app.db.db_Settings.Database")
def test_get_all_parses_boolean_true(mock_database_class, db_config):
    """Test get_all parses boolean true values correctly."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [
        {"key": "bool_true", "value": "true", "value_type": "boolean"},
        {"key": "bool_1", "value": "1", "value_type": "boolean"},
        {"key": "bool_yes", "value": "yes", "value_type": "boolean"},
        {"key": "bool_on", "value": "on", "value_type": "boolean"},
    ]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.get_all()

    assert result["bool_true"] is True
    assert result["bool_1"] is True
    assert result["bool_yes"] is True
    assert result["bool_on"] is True


@patch("src.main_app.db.db_Settings.Database")
def test_get_all_parses_boolean_false(mock_database_class, db_config):
    """Test get_all parses boolean false values correctly."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [
        {"key": "bool_false", "value": "false", "value_type": "boolean"},
        {"key": "bool_0", "value": "0", "value_type": "boolean"},
        {"key": "bool_no", "value": "no", "value_type": "boolean"},
        {"key": "bool_off", "value": "off", "value_type": "boolean"},
    ]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.get_all()

    assert result["bool_false"] is False
    assert result["bool_0"] is False
    assert result["bool_no"] is False
    assert result["bool_off"] is False


@patch("src.main_app.db.db_Settings.Database")
def test_get_all_parses_integer(mock_database_class, db_config):
    """Test get_all parses integer values correctly."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [
        {"key": "int_positive", "value": "42", "value_type": "integer"},
        {"key": "int_negative", "value": "-10", "value_type": "integer"},
        {"key": "int_zero", "value": "0", "value_type": "integer"},
    ]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.get_all()

    assert result["int_positive"] == 42
    assert result["int_negative"] == -10
    assert result["int_zero"] == 0


@patch("src.main_app.db.db_Settings.Database")
def test_get_all_parses_integer_invalid(mock_database_class, db_config):
    """Test get_all handles invalid integer values."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [
        {"key": "int_invalid", "value": "not_a_number", "value_type": "integer"},
    ]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.get_all()

    assert result["int_invalid"] == 0


@patch("src.main_app.db.db_Settings.Database")
def test_get_all_parses_json(mock_database_class, db_config):
    """Test get_all parses JSON values correctly."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [
        {"key": "json_obj", "value": '{"key": "value"}', "value_type": "json"},
        {"key": "json_arr", "value": "[1, 2, 3]", "value_type": "json"},
    ]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.get_all()

    assert result["json_obj"] == {"key": "value"}
    assert result["json_arr"] == [1, 2, 3]


@patch("src.main_app.db.db_Settings.Database")
def test_get_all_parses_json_invalid(mock_database_class, db_config):
    """Test get_all handles invalid JSON values."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [
        {"key": "json_invalid", "value": "not valid json", "value_type": "json"},
    ]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.get_all()

    assert result["json_invalid"] is None


@patch("src.main_app.db.db_Settings.Database")
def test_get_all_parses_string(mock_database_class, db_config):
    """Test get_all returns string values as-is."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [
        {"key": "str_val", "value": "hello world", "value_type": "string"},
    ]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.get_all()

    assert result["str_val"] == "hello world"


@patch("src.main_app.db.db_Settings.Database")
def test_get_all_handles_none(mock_database_class, db_config):
    """Test get_all handles None values."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [
        {"key": "none_val", "value": None, "value_type": "string"},
    ]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.get_all()

    assert result["none_val"] is None


@patch("src.main_app.db.db_Settings.Database")
def test_get_raw_all(mock_database_class, db_config):
    """Test get_raw_all returns all rows."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [
        {
            "id": 1,
            "key": "setting1",
            "title": "Setting 1",
            "value": "val1",
            "value_type": "string",
        },
        {
            "id": 2,
            "key": "setting2",
            "title": "Setting 2",
            "value": "val2",
            "value_type": "boolean",
        },
    ]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.get_raw_all()

    assert len(result) == 2
    assert result[0]["key"] == "setting1"
    assert result[1]["key"] == "setting2"
    mock_db.fetch_query_safe.assert_called_with(
        "SELECT * FROM `settings` ORDER BY `id` ASC"
    )


@patch("src.main_app.db.db_Settings.Database")
def test_get_by_key_found(mock_database_class, db_config):
    """Test get_by_key returns value when key exists."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [
        {"value": "test_value", "value_type": "string"}
    ]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.get_by_key("test_key")

    assert result == "test_value"
    mock_db.fetch_query_safe.assert_called_with(
        "SELECT `value`, `value_type` FROM `settings` WHERE `key` = %s", ("test_key",)
    )


@patch("src.main_app.db.db_Settings.Database")
def test_get_by_key_not_found(mock_database_class, db_config):
    """Test get_by_key returns None when key doesn't exist."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = []
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.get_by_key("missing_key")

    assert result is None


@patch("src.main_app.db.db_Settings.Database")
def test_create_setting_success(mock_database_class, db_config):
    """Test create_setting returns True on success."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = []  # get_by_key returns no existing key
    mock_db.execute_query_safe.return_value = 1  # affected_rows > 0
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.create_setting("new_key", "New Setting", "boolean", True)

    assert result is True
    mock_db.execute_query_safe.assert_any_call(
        "INSERT INTO `settings` (`key`, `title`, `value_type`, `value`) VALUES (%s, %s, %s, %s)",
        ("new_key", "New Setting", "boolean", "true"),
    )


@patch("src.main_app.db.db_Settings.Database")
def test_create_setting_failure(mock_database_class, db_config):
    """Test create_setting returns False on failure."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    # Now set the side_effect for the create operation
    mock_db.execute_query_safe.side_effect = Exception("DB Error")
    result = settings_db.create_setting("new_key", "New Setting", "string", "value")

    assert result is False


@patch("src.main_app.db.db_Settings.Database")
def test_create_setting_serialize_boolean(mock_database_class, db_config):
    """Test create_setting serializes boolean values correctly."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = []  # get_by_key returns no existing key
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    settings_db.create_setting("bool_key", "Bool Setting", "boolean", True)
    settings_db.create_setting("bool_key2", "Bool Setting 2", "boolean", False)

    calls = mock_db.execute_query_safe.call_args_list
    # First call is CREATE TABLE from __init__
    # Second and third calls are the INSERT statements
    assert calls[1][0][1][3] == "true"
    assert calls[2][0][1][3] == "false"


@patch("src.main_app.db.db_Settings.Database")
def test_create_setting_serialize_integer(mock_database_class, db_config):
    """Test create_setting serializes integer values correctly."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = []  # get_by_key returns no existing key
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    settings_db.create_setting("int_key", "Int Setting", "integer", 42)

    calls = mock_db.execute_query_safe.call_args_list
    # First call is CREATE TABLE, second is INSERT
    assert calls[1][0][1][3] == "42"


@patch("src.main_app.db.db_Settings.Database")
def test_create_setting_serialize_json(mock_database_class, db_config):
    """Test create_setting serializes JSON values correctly."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = []  # get_by_key returns no existing key
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    settings_db.create_setting("json_key", "JSON Setting", "json", {"key": "value"})

    calls = mock_db.execute_query_safe.call_args_list
    # First call is CREATE TABLE, second is INSERT
    assert calls[1][0][1][3] == '{"key": "value"}'


@patch("src.main_app.db.db_Settings.Database")
def test_update_setting_success(mock_database_class, db_config):
    """Test update_setting returns True on success."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [{"value_type": "string"}]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.update_setting("existing_key", "new_value")

    assert result is True
    mock_db.execute_query_safe.assert_called_with(
        "UPDATE `settings` SET `value` = %s WHERE `key` = %s",
        ("new_value", "existing_key"),
    )


@patch("src.main_app.db.db_Settings.Database")
def test_update_setting_not_found(mock_database_class, db_config):
    """Test update_setting returns False when key doesn't exist."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = []
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.update_setting("missing_key", "value")

    assert result is False


@patch("src.main_app.db.db_Settings.Database")
def test_update_setting_failure(mock_database_class, db_config):
    """Test update_setting returns False on failure."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [{"value_type": "string"}]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    # Set the side_effect for the update operation after init
    mock_db.execute_query_safe.side_effect = Exception("DB Error")
    result = settings_db.update_setting("existing_key", "value")

    assert result is False


@patch("src.main_app.db.db_Settings.Database")
def test_update_setting_preserves_type(mock_database_class, db_config):
    """Test update_setting uses existing value_type from database."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [{"value_type": "integer"}]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    settings_db.update_setting("int_key", 100)

    # Verify the value was serialized as integer
    calls = mock_db.execute_query_safe.call_args_list
    assert calls[1][0][1] == ("100", "int_key")


@patch("src.main_app.db.db_Settings.Database")
def test_update_setting_with_value_type_skips_select(mock_database_class, db_config):
    """Test update_setting skips SELECT when value_type is provided."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.update_setting("key", "value", value_type="string")

    assert result is True
    # Should only have the UPDATE call, no SELECT call
    mock_db.fetch_query_safe.assert_not_called()
    # Second call (first is CREATE TABLE) should be the UPDATE
    mock_db.execute_query_safe.assert_any_call(
        "UPDATE `settings` SET `value` = %s WHERE `key` = %s",
        ("value", "key"),
    )
    # Total of 2 calls: CREATE TABLE and UPDATE
    assert mock_db.execute_query_safe.call_count == 2


@patch("src.main_app.db.db_Settings.Database")
def test_update_setting_without_value_type_queries_db(mock_database_class, db_config):
    """Test update_setting performs SELECT when value_type is not provided."""
    mock_db = MagicMock()
    mock_db.fetch_query_safe.return_value = [{"value_type": "integer"}]
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db.update_setting("key", 42)

    assert result is True
    # Should have SELECT call to get value_type
    mock_db.fetch_query_safe.assert_called_once_with(
        "SELECT `value_type` FROM `settings` WHERE `key` = %s", ("key",)
    )
    # Value should be serialized as integer
    mock_db.execute_query_safe.assert_any_call(
        "UPDATE `settings` SET `value` = %s WHERE `key` = %s",
        ("42", "key"),
    )
    # Total of 2 calls: CREATE TABLE and UPDATE
    assert mock_db.execute_query_safe.call_count == 2


@patch("src.main_app.db.db_Settings.Database")
def test_update_setting_with_value_type_serializes_correctly(
    mock_database_class, db_config
):
    """Test update_setting uses provided value_type for serialization."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    # Pass integer value with explicit boolean type
    result = settings_db.update_setting("key", 1, value_type="boolean")

    assert result is True
    # Value should be serialized as boolean "true", not as integer "1"
    mock_db.execute_query_safe.assert_any_call(
        "UPDATE `settings` SET `value` = %s WHERE `key` = %s",
        ("true", "key"),
    )
    # Total of 2 calls: CREATE TABLE and UPDATE
    assert mock_db.execute_query_safe.call_count == 2


@patch("src.main_app.db.db_Settings.Database")
def test_serialize_value_none(mock_database_class, db_config):
    """Test _serialize_value handles None."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)
    result = settings_db._serialize_value(None, "string")

    assert result is None


@patch("src.main_app.db.db_Settings.Database")
def test_serialize_value_boolean(mock_database_class, db_config):
    """Test _serialize_value handles booleans."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)

    assert settings_db._serialize_value(True, "boolean") == "true"
    assert settings_db._serialize_value(False, "boolean") == "false"


@patch("src.main_app.db.db_Settings.Database")
def test_serialize_value_integer(mock_database_class, db_config):
    """Test _serialize_value handles integers."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)

    assert settings_db._serialize_value(42, "integer") == "42"
    assert settings_db._serialize_value(-10, "integer") == "-10"


@patch("src.main_app.db.db_Settings.Database")
def test_serialize_value_json(mock_database_class, db_config):
    """Test _serialize_value handles JSON."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)

    assert settings_db._serialize_value({"key": "value"}, "json") == '{"key": "value"}'
    assert settings_db._serialize_value([1, 2, 3], "json") == "[1, 2, 3]"


@patch("src.main_app.db.db_Settings.Database")
def test_serialize_value_string(mock_database_class, db_config):
    """Test _serialize_value handles strings."""
    mock_db = MagicMock()
    mock_database_class.return_value = mock_db

    settings_db = SettingsDB(db_config)

    assert settings_db._serialize_value("hello", "string") == "hello"
    assert settings_db._serialize_value(123, "string") == "123"
