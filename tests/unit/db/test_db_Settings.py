"""Tests for SettingsDB database operations."""

from unittest.mock import MagicMock

import pytest

from src.main_app.db.db_Settings import SettingsDB
from src.main_app.db.models import SettingRecord
from src.main_app.db.engine_sqlite import DatabaseSqlLite


@pytest.fixture
def mock_db_instance():
    return MagicMock(spec=DatabaseSqlLite)


@pytest.fixture
def settings_db(mock_db_instance):
    return SettingsDB(db=mock_db_instance)


def test_get_all_parses_boolean_true(mock_db_instance, settings_db):
    """Test get_all parses boolean true values correctly."""

    mock_db_instance.fetch_query_safe.return_value = [
        {"key": "bool_true", "value": "true", "value_type": "boolean"},
        {"key": "bool_1", "value": "1", "value_type": "boolean"},
        {"key": "bool_yes", "value": "yes", "value_type": "boolean"},
        {"key": "bool_on", "value": "on", "value_type": "boolean"},
    ]

    result = settings_db.get_all()

    assert result["bool_true"] is True
    assert result["bool_1"] is True
    assert result["bool_yes"] is True
    assert result["bool_on"] is True


def test_get_all_parses_boolean_false(mock_db_instance, settings_db):
    """Test get_all parses boolean false values correctly."""

    mock_db_instance.fetch_query_safe.return_value = [
        {"key": "bool_false", "value": "false", "value_type": "boolean"},
        {"key": "bool_0", "value": "0", "value_type": "boolean"},
        {"key": "bool_no", "value": "no", "value_type": "boolean"},
        {"key": "bool_off", "value": "off", "value_type": "boolean"},
    ]

    result = settings_db.get_all()

    assert result["bool_false"] is False
    assert result["bool_0"] is False
    assert result["bool_no"] is False
    assert result["bool_off"] is False


def test_get_all_parses_integer(mock_db_instance, settings_db):
    """Test get_all parses integer values correctly."""

    mock_db_instance.fetch_query_safe.return_value = [
        {"key": "int_positive", "value": "42", "value_type": "integer"},
        {"key": "int_negative", "value": "-10", "value_type": "integer"},
        {"key": "int_zero", "value": "0", "value_type": "integer"},
    ]

    result = settings_db.get_all()

    assert result["int_positive"] == 42
    assert result["int_negative"] == -10
    assert result["int_zero"] == 0


def test_get_all_parses_integer_invalid(mock_db_instance, settings_db):
    """Test get_all handles invalid integer values."""

    mock_db_instance.fetch_query_safe.return_value = [
        {"key": "int_invalid", "value": "not_a_number", "value_type": "integer"},
    ]

    result = settings_db.get_all()

    assert result["int_invalid"] == 0


def test_get_all_parses_json(mock_db_instance, settings_db):
    """Test get_all parses JSON values correctly."""

    mock_db_instance.fetch_query_safe.return_value = [
        {"key": "json_obj", "value": '{"key": "value"}', "value_type": "json"},
        {"key": "json_arr", "value": "[1, 2, 3]", "value_type": "json"},
    ]

    result = settings_db.get_all()

    assert result["json_obj"] == {"key": "value"}
    assert result["json_arr"] == [1, 2, 3]


def test_get_all_parses_json_invalid(mock_db_instance, settings_db):
    """Test get_all handles invalid JSON values."""

    mock_db_instance.fetch_query_safe.return_value = [
        {"key": "json_invalid", "value": "not valid json", "value_type": "json"},
    ]

    result = settings_db.get_all()

    assert result["json_invalid"] is None


def test_get_all_parses_string(mock_db_instance, settings_db):
    """Test get_all returns string values as-is."""

    mock_db_instance.fetch_query_safe.return_value = [
        {"key": "str_val", "value": "hello world", "value_type": "string"},
    ]

    result = settings_db.get_all()

    assert result["str_val"] == "hello world"


def test_get_all_handles_none(mock_db_instance, settings_db):
    """Test get_all handles None values."""

    mock_db_instance.fetch_query_safe.return_value = [
        {"key": "none_val", "value": None, "value_type": "string"},
    ]

    result = settings_db.get_all()

    assert result["none_val"] is None


def test_get_raw_all(mock_db_instance, settings_db):
    """Test get_raw_all returns all rows."""

    mock_db_instance.fetch_query_safe.return_value = [
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

    result = settings_db.get_raw_all()

    assert len(result) == 2
    assert result[0]["key"] == "setting1"
    assert result[1]["key"] == "setting2"
    mock_db_instance.fetch_query_safe.assert_called_with(
        "SELECT id, key, title, value_type, value FROM settings ORDER BY id ASC"
    )


def test_get_by_key_found(mock_db_instance, settings_db):
    """Test get_by_key returns value when key exists."""

    mock_db_instance.fetch_query_safe.return_value = [{"id": 1, "key": "key", "value": "test_value", "value_type": "string"}]

    result = settings_db.get_by_key("test_key")

    assert result == SettingRecord(id=1, key="key", title=None, value_type="string", value="test_value")
    mock_db_instance.fetch_query_safe.assert_called_with(
        "SELECT id, key, title, value_type, value FROM settings WHERE key = %s", ("test_key",)
    )


def test_get_by_key_not_found(mock_db_instance, settings_db):
    """Test get_by_key returns None when key doesn't exist."""

    mock_db_instance.fetch_query_safe.return_value = []

    result = settings_db.get_by_key("missing_key")

    assert result is None


def test_create_setting_success(mock_db_instance, settings_db):
    """Test create_setting returns True on success."""

    mock_db_instance.fetch_query_safe.return_value = []  # get_by_key returns no existing key
    mock_db_instance.execute_query_safe.return_value = 1  # affected_rows > 0

    result = settings_db.create(key="new_key", title="New Setting", value_type="boolean", value="true")

    assert result is True
    mock_db_instance.insert_query.assert_any_call(
        "INSERT INTO settings (key, title, value_type, value) VALUES (%s, %s, %s, %s)",
        ("new_key", "New Setting", "boolean", "true"),
    )


def test_create_setting_failure(mock_db_instance, settings_db):
    """Test create_setting returns False on failure."""

    # Now set the side_effect for the create operation
    mock_db_instance.execute_query_safe.side_effect = Exception("DB Error")
    # with pytest.raises(ValueError, match="Invalid value_type:"):
    result = settings_db.create(key="new_key", title="New Setting", value_type="stringz", value="value")
    assert result is False


def test_create_setting_serialize_boolean(mock_db_instance, settings_db):
    """Test create_setting serializes boolean values correctly."""

    mock_db_instance.fetch_query_safe.return_value = []  # get_by_key returns no existing key

    settings_db.create(key="bool_key", title="Bool Setting", value_type="boolean", value="true")
    settings_db.create(key="bool_key2", title="Bool Setting 2", value_type="boolean", value="false")

    calls = mock_db_instance.execute_query_safe.call_args_list
    # First call is CREATE TABLE from __init__
    # Second and third calls are the INSERT statements
    assert calls[1][0][1][3] == "true"
    assert calls[2][0][1][3] == "false"


def test_create_setting_serialize_integer(mock_db_instance, settings_db):
    """Test create_setting serializes integer values correctly."""

    mock_db_instance.fetch_query_safe.return_value = []  # get_by_key returns no existing key

    settings_db.create(key="int_key", title="Int Setting", value_type="integer", value="42")

    calls = mock_db_instance.execute_query_safe.call_args_list
    # First call is CREATE TABLE, second is INSERT
    assert calls[1][0][1][3] == "42"


def test_create_setting_serialize_json(mock_db_instance, settings_db):
    """Test create_setting serializes JSON values correctly."""

    mock_db_instance.fetch_query_safe.return_value = []  # get_by_key returns no existing key

    settings_db.create(key="json_key", title="JSON Setting", value_type="json", value='{"key": "value"}')

    calls = mock_db_instance.execute_query_safe.call_args_list
    # First call is CREATE TABLE, second is INSERT
    assert calls[1][0][1][3] == '{"key": "value"}'


class TestUpdate:

    def test_update_setting_success(self, mock_db_instance, settings_db):
        """Test update_setting returns True on success."""

        mock_db_instance.fetch_query_safe.return_value = [{"id": 1, "key": "key", "value_type": "string", "value": "value"}]

        result = settings_db.update("existing_key", "new_value")

        assert result is True
        mock_db_instance.execute_query_safe.assert_called_with(
            "UPDATE settings SET value = %s WHERE key = %s",
            ("new_value", "existing_key"),
        )

    def test_update_setting_not_found(self, mock_db_instance, settings_db):
        """Test update_setting returns False when key doesn't exist."""

        mock_db_instance.fetch_query_safe.return_value = []

        result = settings_db.update("missing_key", "value")

        assert result is False

    def test_update_setting_failure(self, mock_db_instance, settings_db):
        """Test update_setting returns False on failure."""

        mock_db_instance.fetch_query_safe.return_value = [{"id": 1, "key": "key", "value_type": "string", "value": "value"}]

        # Set the side_effect for the update operation after init
        mock_db_instance.execute_query_safe.side_effect = Exception("DB Error")
        result = settings_db.update("existing_key", "value")

        assert result is False

    def test_update_setting_preserves_type(self, mock_db_instance, settings_db):
        """Test update_setting uses existing value_type from database."""

        mock_db_instance.fetch_query_safe.return_value = [{"id": 1, "key": "key", "value_type": "integer", "value": "0"}]

        settings_db.update("int_key", "100")

        # Verify the value was serialized as integer
        calls = mock_db_instance.execute_query_safe.call_args_list
        assert calls[1][0][1] == ("100", "int_key")

    def test_update_setting_with_value_type_skips_select(self, mock_db_instance, settings_db):
        """Test update_setting skips SELECT when value_type is provided."""

        result = settings_db.update(key="key", value="value", title="")

        assert result is True
        # Second call (first is CREATE TABLE) should be the UPDATE
        mock_db_instance.execute_query_safe.assert_any_call(
            "UPDATE settings SET value = %s WHERE key = %s",
            ("value", "key"),
        )
        # Should only have the UPDATE call, no SELECT call
        mock_db_instance.fetch_query_safe.assert_called_with(
            "SELECT id, key, title, value_type, value FROM settings WHERE key = %s",
            ("key"),
        )
        # Total of 2 calls: CREATE TABLE and UPDATE
        assert mock_db_instance.execute_query_safe.call_count == 2

    def test_update_setting_without_value_type_queries_db(self, mock_db_instance, settings_db):
        """Test update_setting performs SELECT when value_type is not provided."""

        mock_db_instance.fetch_query_safe.return_value = [{"id": 1, "key": "key", "value_type": "integer", "value": "0"}]

        result = settings_db.update(key="key", value="42")

        assert result is True
        # Should have SELECT call to get value_type
        mock_db_instance.fetch_query_safe.assert_called_once_with(
            "SELECT id, key, title, value_type, value FROM settings WHERE key = %s", ("key")
        )
        # Value should be serialized as integer
        mock_db_instance.execute_query_safe.assert_any_call(
            "UPDATE settings SET value = %s WHERE key = %s",
            ("42", "key"),
        )
        # Total of 2 calls: CREATE TABLE and UPDATE
        assert mock_db_instance.execute_query_safe.call_count == 2

    def test_update_setting_with_value_type_serializes_correctly(self, mock_db_instance, settings_db):
        """Test update_setting uses provided value_type for serialization."""

        # Pass integer value with explicit boolean type
        result = settings_db.update(key="key", value="true")

        assert result is True
        # Value should be serialized as boolean "true", not as integer "1"
        mock_db_instance.execute_query_safe.assert_any_call(
            "UPDATE settings SET value = %s WHERE key = %s",
            ("true", "key"),
        )
        # Total of 2 calls: CREATE TABLE and UPDATE
        assert mock_db_instance.execute_query_safe.call_count == 2
