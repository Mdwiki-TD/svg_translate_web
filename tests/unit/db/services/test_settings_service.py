from __future__ import annotations

import pytest

from src.main_app.db.models import SettingRecord
from src.main_app.db.services.settings_service import SettingsService, _serialize_value
from src.main_app.extensions import db


@pytest.fixture
def setting_record() -> SettingRecord:
    record = SettingRecord(key="test_key", title="Test Setting", value_type="string", value="test_value")
    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = SettingsService()


class TestListSettingsReady(TestSetup):
    def test_get_all_settings_ready(self) -> None:
        self.service.create_setting(
            "crop_newest_upload_limit", "Crop Newest World Files upload limit", "integer", "5000"
        )
        records_raw = self.service.get_all_settings_raw()
        assert records_raw[0]["value"] == "5000"

        records = self.service.get_all_settings_ready()
        assert records == {"crop_newest_upload_limit": 5000}


class TestListSettings(TestSetup):
    """Tests for list_settings."""

    def test_list_settings(self, setting_record: SettingRecord) -> None:
        result = self.service.list_settings()
        assert len(result) == 1
        assert result[0].id == setting_record.id
        assert result[0].key == setting_record.key


class TestGetAllSettingsRaw(TestSetup):
    """Tests for get_all_settings_raw."""

    def test_returns_to_dict_of_all_settings(self) -> None:
        self.service.create_setting("setting1", "Setting 1", "string", "val1")
        self.service.create_setting("setting2", "Setting 2", "string", "val2")

        result = self.service.get_all_settings_raw()

        assert {record["key"]: record["value"] for record in result} == {"setting1": "val1", "setting2": "val2"}


class TestGetAllSettingsReady(TestSetup):
    """Tests for get_all_settings_ready parsing logic."""

    def test_boolean_true(self) -> None:
        self.service.create_setting("test_bool", "Test Bool", "boolean", "true")
        assert self.service.get_all_settings_ready() == {"test_bool": True}

    def test_boolean_false(self) -> None:
        self.service.create_setting("test_bool", "Test Bool", "boolean", "false")
        assert self.service.get_all_settings_ready() == {"test_bool": False}

    def test_integer_from_string(self) -> None:
        self.service.create_setting("test_int", "Test Int", "integer", "42")
        assert self.service.get_all_settings_ready() == {"test_int": 42}

    def test_integer_invalid(self, caplog: pytest.LogCaptureFixture) -> None:
        self.service.create_setting("test_int", "Test Int", "integer", "not_a_number")
        with caplog.at_level("WARNING"):
            result = self.service.get_all_settings_ready()
        assert result == {"test_int": None}
        assert "Could not parse setting test_int with value not_a_number" in caplog.text

    def test_string(self) -> None:
        self.service.create_setting("test_str", "Test Str", "string", "hello")
        assert self.service.get_all_settings_ready() == {"test_str": "hello"}


class TestGetSettingByKey(TestSetup):
    """Tests for get_setting_by_key."""

    def test_returns_setting_by_key(self, setting_record: SettingRecord) -> None:
        result = self.service.get_setting_by_key(setting_record.key)
        assert result is not None
        assert result.id == setting_record.id

    def test_returns_none_for_missing_key(self) -> None:
        result = self.service.get_setting_by_key("nonexistent")
        assert result is None


class TestUpdateSetting(TestSetup):
    """Tests for update_setting."""

    def test_updates_existing_setting(self, setting_record: SettingRecord) -> None:
        result = self.service.update_setting(setting_record.key, "new_value", "string", "New Title")

        assert result is not False
        assert result.value == "new_value"
        assert result.title == "New Title"

    def test_returns_false_when_not_found(self) -> None:
        result = self.service.update_setting("nonexistent", "value")
        assert result is False

    def test_serializes_value_according_to_type(self, setting_record: SettingRecord) -> None:
        result = self.service.update_setting(setting_record.key, True, "boolean")
        assert result is not False
        assert result.value == "true"

    def test_uses_existing_value_type_when_none_provided(self, setting_record: SettingRecord) -> None:
        setting_record.value_type = "integer"
        db.session.commit()

        result = self.service.update_setting(setting_record.key, 99, value_type=None)
        assert result is not False
        assert result.value == "99"


class TestCreateSetting(TestSetup):
    """Tests for create_setting."""

    def test_creates_setting_successfully(self) -> None:
        result = self.service.create_setting("test_key", "Test Title", "string", "test_value")

        assert result is not None
        assert result.key == "test_key"
        assert result.title == "Test Title"
        assert result.value == "test_value"
        assert result.value_type == "string"
        assert db.session.get(SettingRecord, result.id) is not None

    def test_handles_exception_rollback(self, setting_record: SettingRecord) -> None:
        result = self.service.create_setting(setting_record.key, "Test Title", "string", "test_value")

        assert result is None
        assert db.session.is_active is True

    def test_default_value_boolean(self) -> None:
        result = self.service.create_setting("bool_key", "Bool Setting", "boolean")
        assert result.value == "false"

    def test_default_value_integer(self) -> None:
        result = self.service.create_setting("int_key", "Int Setting", "integer")
        assert result.value == "0"

    def test_default_value_string(self) -> None:
        result = self.service.create_setting("str_key", "Str Setting", "string")
        assert result.value == ""

    def test_requires_key(self) -> None:
        with pytest.raises(ValueError, match="Key is required"):
            self.service.create_setting("  ", "Title", "string")

    def test_requires_title(self) -> None:
        with pytest.raises(ValueError, match="Title is required"):
            self.service.create_setting("key", "  ", "string")


class TestSerializeValue:
    """Test _serialize_value function."""

    def test_serialize_value_none(self) -> None:
        """Test _serialize_value handles None."""
        result = _serialize_value(None, "string")
        assert result is None

    def test_serialize_value_boolean(self) -> None:
        """Test _serialize_value handles booleans."""
        assert _serialize_value(True, "boolean") == "true"
        assert _serialize_value(False, "boolean") == "false"

    def test_serialize_value_integer(self) -> None:
        """Test _serialize_value handles integers."""
        assert _serialize_value(42, "integer") == "42"
        assert _serialize_value(-10, "integer") == "-10"

    def test_serialize_value_string(self) -> None:
        """Test _serialize_value handles strings."""
        assert _serialize_value("hello", "string") == "hello"
        assert _serialize_value(123, "string") == "123"
