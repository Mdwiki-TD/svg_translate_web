
from src.main_app.db.services.settings_service import (
    _serialize_value,
    create_setting,
    get_all_settings_raw,
    get_all_settings_ready,
)


def test_serialize_value_none():
    """Test _serialize_value handles None."""
    result = _serialize_value(None, "string")
    assert result is None


def test_serialize_value_boolean():
    """Test _serialize_value handles booleans."""
    assert _serialize_value(True, "boolean") == "true"
    assert _serialize_value(False, "boolean") == "false"


def test_serialize_value_integer():
    """Test _serialize_value handles integers."""
    assert _serialize_value(42, "integer") == "42"
    assert _serialize_value(-10, "integer") == "-10"


def test_serialize_value_string():
    """Test _serialize_value handles strings."""
    assert _serialize_value("hello", "string") == "hello"
    assert _serialize_value(123, "string") == "123"


def test_get_all_settings_ready() -> None:
    create_setting("crop_newest_upload_limit", "Crop Newest World Files upload limit", "integer", "5000")
    records_raw = get_all_settings_raw()
    assert records_raw[0]["value"] == "5000"

    records = get_all_settings_ready()
    assert records == {"crop_newest_upload_limit": 5000}
