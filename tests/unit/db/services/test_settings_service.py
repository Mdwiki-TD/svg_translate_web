from unittest.mock import MagicMock

from src.main_app.db.services.settings_service import (
    _parse_setting_value,
    _serialize_value,
    create_setting,
    get_all_settings_raw,
    get_all_settings_ready,
    get_setting_by_key,
    list_settings,
    settings_update_form,
    update_setting,
    update_setting_bool,
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


class TestParseSettingValue:
    """Tests for _parse_setting_value."""

    def test_boolean_on(self):
        assert _parse_setting_value("boolean", "on") == (True, True)

    def test_boolean_off(self):
        assert _parse_setting_value("boolean", "off") == (False, True)

    def test_boolean_empty(self):
        assert _parse_setting_value("boolean", "") == (False, True)

    def test_boolean_other(self):
        assert _parse_setting_value("boolean", "true") == (False, True)

    def test_integer_valid(self):
        assert _parse_setting_value("integer", "42") == (42, True)

    def test_integer_negative(self):
        assert _parse_setting_value("integer", "-10") == (-10, True)

    def test_integer_invalid(self):
        assert _parse_setting_value("integer", "abc") == (0, True)

    def test_integer_empty(self):
        assert _parse_setting_value("integer", "") == (0, True)

    def test_string(self):
        assert _parse_setting_value("string", "hello") == ("hello", True)

    def test_unknown_type(self):
        assert _parse_setting_value("unknown", "raw") == ("raw", True)


class TestListSettings:
    """Tests for list_settings."""

    def test_list_settings(self, monkeypatch):
        mock_records = [MagicMock(), MagicMock()]
        mock_query = MagicMock()
        mock_query.all.return_value = mock_records
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.query", lambda cls: mock_query)
        result = list_settings()
        assert result == mock_records


class TestGetAllSettingsRaw:
    """Tests for get_all_settings_raw."""

    def test_returns_to_dict_of_all_settings(self, monkeypatch):
        mock_record1 = MagicMock()
        mock_record1.to_dict.return_value = {"key": "setting1", "value": "val1"}
        mock_record2 = MagicMock()
        mock_record2.to_dict.return_value = {"key": "setting2", "value": "val2"}
        monkeypatch.setattr(
            "src.main_app.db.services.settings_service.list_settings", lambda: [mock_record1, mock_record2]
        )
        result = get_all_settings_raw()
        assert result == [{"key": "setting1", "value": "val1"}, {"key": "setting2", "value": "val2"}]


class TestGetAllSettingsReady:
    """Tests for get_all_settings_ready parsing logic."""

    def test_boolean_true(self, monkeypatch):
        mock_record = MagicMock()
        mock_record.value_type = "boolean"
        mock_record.value = "true"
        mock_record.key = "test_bool"
        monkeypatch.setattr("src.main_app.db.services.settings_service.list_settings", lambda: [mock_record])
        assert get_all_settings_ready() == {"test_bool": True}

    def test_boolean_false(self, monkeypatch):
        mock_record = MagicMock()
        mock_record.value_type = "boolean"
        mock_record.value = "false"
        mock_record.key = "test_bool"
        monkeypatch.setattr("src.main_app.db.services.settings_service.list_settings", lambda: [mock_record])
        assert get_all_settings_ready() == {"test_bool": False}

    def test_integer_from_string(self, monkeypatch):
        mock_record = MagicMock()
        mock_record.value_type = "integer"
        mock_record.value = "42"
        mock_record.key = "test_int"
        monkeypatch.setattr("src.main_app.db.services.settings_service.list_settings", lambda: [mock_record])
        assert get_all_settings_ready() == {"test_int": 42}

    def test_integer_from_int(self, monkeypatch):
        mock_record = MagicMock()
        mock_record.value_type = "integer"
        mock_record.value = 42
        mock_record.key = "test_int"
        monkeypatch.setattr("src.main_app.db.services.settings_service.list_settings", lambda: [mock_record])
        assert get_all_settings_ready() == {"test_int": 42}

    def test_integer_invalid(self, monkeypatch, caplog):
        mock_record = MagicMock()
        mock_record.value_type = "integer"
        mock_record.value = "not_a_number"
        mock_record.key = "test_int"
        monkeypatch.setattr("src.main_app.db.services.settings_service.list_settings", lambda: [mock_record])
        with caplog.at_level("WARNING"):
            result = get_all_settings_ready()
        assert result == {"test_int": None}
        assert "Could not parse setting test_int with value not_a_number" in caplog.text

    def test_string(self, monkeypatch):
        mock_record = MagicMock()
        mock_record.value_type = "string"
        mock_record.value = "hello"
        mock_record.key = "test_str"
        monkeypatch.setattr("src.main_app.db.services.settings_service.list_settings", lambda: [mock_record])
        assert get_all_settings_ready() == {"test_str": "hello"}

    def test_unknown_type_logs_warning(self, monkeypatch, caplog):
        mock_record = MagicMock()
        mock_record.value_type = "unknown"
        mock_record.value = "anything"
        mock_record.key = "test_unknown"
        monkeypatch.setattr("src.main_app.db.services.settings_service.list_settings", lambda: [mock_record])
        with caplog.at_level("WARNING"):
            result = get_all_settings_ready()
        assert result == {"test_unknown": None}
        assert "Could not parse setting test_unknown with value anything" in caplog.text


class TestGetSettingByKey:
    """Tests for get_setting_by_key."""

    def test_returns_setting_by_key(self, monkeypatch):
        mock_setting = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_setting
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.query", lambda cls: mock_query)
        result = get_setting_by_key("test_key")
        assert result == mock_setting

    def test_returns_none_for_missing_key(self, monkeypatch):
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.query", lambda cls: mock_query)
        result = get_setting_by_key("nonexistent")
        assert result is None


class TestUpdateSetting:
    """Tests for update_setting (wrapped with @db_guard)."""

    def test_updates_existing_setting(self, monkeypatch):
        mock_setting = MagicMock()
        mock_setting.value = None
        mock_setting.title = "Original"
        mock_setting.value_type = "string"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_setting
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.query", lambda cls: mock_query)
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.commit", lambda: None)

        result = update_setting("test_key", "new_value", "string", "New Title")

        assert mock_setting.value == "new_value"
        assert mock_setting.title == "New Title"
        assert result == mock_setting

    def test_returns_false_when_not_found(self, monkeypatch):
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.query", lambda cls: mock_query)

        result = update_setting("nonexistent", "value")
        assert result is False

    def test_serializes_value_according_to_type(self, monkeypatch):
        mock_setting = MagicMock()
        mock_setting.value = None
        mock_setting.title = "Orig"
        mock_setting.value_type = "boolean"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_setting
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.query", lambda cls: mock_query)
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.commit", lambda: None)

        update_setting("test_key", True, "boolean")
        assert mock_setting.value == "true"

    def test_uses_existing_value_type_when_none_provided(self, monkeypatch):
        mock_setting = MagicMock()
        mock_setting.value = None
        mock_setting.title = "Orig"
        mock_setting.value_type = "integer"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_setting
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.query", lambda cls: mock_query)
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.commit", lambda: None)

        update_setting("test_key", 99, value_type=None)
        assert mock_setting.value == "99"


class TestUpdateSettingBool:
    """Tests for update_setting_bool (wrapped with @db_guard_rollback)."""

    def test_updates_existing_setting(self, monkeypatch):
        mock_setting = MagicMock()
        mock_setting.value = None
        mock_setting.title = "Original"
        mock_setting.value_type = "boolean"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_setting
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.query", lambda cls: mock_query)
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.commit", lambda: None)

        result = update_setting_bool("test_key", True, "boolean")

        assert mock_setting.value == "true"
        assert result is True

    def test_returns_false_when_not_found(self, monkeypatch):
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.query", lambda cls: mock_query)

        result = update_setting_bool("nonexistent", True)
        assert result is False


class TestCreateSetting:
    """Tests for create_setting."""

    def test_creates_setting_successfully(self, monkeypatch):
        added_settings = []
        monkeypatch.setattr(
            "src.main_app.db.services.settings_service.db.session.add", lambda s: added_settings.append(s)
        )
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.commit", lambda: None)

        result = create_setting("test_key", "Test Title", "string", "test_value")

        assert result is True
        assert len(added_settings) == 1
        assert added_settings[0].key == "test_key"
        assert added_settings[0].title == "Test Title"
        assert added_settings[0].value == "test_value"
        assert added_settings[0].value_type == "string"

    def test_handles_exception_rollback(self, monkeypatch):
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.add", lambda s: None)
        monkeypatch.setattr(
            "src.main_app.db.services.settings_service.db.session.commit",
            MagicMock(side_effect=Exception("DB error")),
        )
        rollback = MagicMock()
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.rollback", rollback)

        result = create_setting("test_key", "Test Title", "string", "test_value")

        assert result is False
        rollback.assert_called_once()

    def test_default_value_boolean(self, monkeypatch):
        added_settings = []
        monkeypatch.setattr(
            "src.main_app.db.services.settings_service.db.session.add", lambda s: added_settings.append(s)
        )
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.commit", lambda: None)

        create_setting("bool_key", "Bool Setting", "boolean")
        assert added_settings[0].value == "false"

    def test_default_value_integer(self, monkeypatch):
        added_settings = []
        monkeypatch.setattr(
            "src.main_app.db.services.settings_service.db.session.add", lambda s: added_settings.append(s)
        )
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.commit", lambda: None)

        create_setting("int_key", "Int Setting", "integer")
        assert added_settings[0].value == "0"

    def test_default_value_string(self, monkeypatch):
        added_settings = []
        monkeypatch.setattr(
            "src.main_app.db.services.settings_service.db.session.add", lambda s: added_settings.append(s)
        )
        monkeypatch.setattr("src.main_app.db.services.settings_service.db.session.commit", lambda: None)

        create_setting("str_key", "Str Setting", "string")
        assert added_settings[0].value == ""


class TestSettingsUpdateForm:
    """Tests for settings_update_form."""

    def test_processes_boolean_value(self, monkeypatch):
        mock_settings = [
            {"key": "test_bool", "value_type": "boolean", "value": "false"},
        ]
        monkeypatch.setattr("src.main_app.db.services.settings_service.get_all_settings_raw", lambda: mock_settings)

        updated = {}

        def mock_update(key, value, v_type):
            updated[key] = (value, v_type)
            return True

        monkeypatch.setattr("src.main_app.db.services.settings_service.update_setting", mock_update)

        request_form = {"setting_test_bool": "on"}

        failed, deleted = settings_update_form(request_form)

        assert failed == []
        assert deleted == []
        assert updated == {"test_bool": (True, "boolean")}

    def test_processes_integer_value(self, monkeypatch):
        mock_settings = [
            {"key": "test_int", "value_type": "integer", "value": "0"},
        ]
        monkeypatch.setattr("src.main_app.db.services.settings_service.get_all_settings_raw", lambda: mock_settings)

        updated = {}

        def mock_update(key, value, v_type):
            updated[key] = (value, v_type)
            return True

        monkeypatch.setattr("src.main_app.db.services.settings_service.update_setting", mock_update)

        request_form = {"setting_test_int": "42"}

        failed, deleted = settings_update_form(request_form)

        assert failed == []
        assert deleted == []
        assert updated == {"test_int": (42, "integer")}

    def test_handles_delete_action(self, monkeypatch):
        mock_settings = [
            {"key": "test_key", "value_type": "string", "value": "val"},
        ]
        monkeypatch.setattr("src.main_app.db.services.settings_service.get_all_settings_raw", lambda: mock_settings)
        monkeypatch.setattr("src.main_app.db.services.settings_service.delete_setting", lambda k: True)

        request_form = {"delete_test_key": "on"}

        failed, deleted = settings_update_form(request_form)

        assert failed == []
        assert deleted == ["test_key"]

    def test_collects_failed_keys_on_error(self, monkeypatch):
        mock_settings = [
            {"key": "test_key", "value_type": "string", "value": "val"},
        ]
        monkeypatch.setattr("src.main_app.db.services.settings_service.get_all_settings_raw", lambda: mock_settings)
        monkeypatch.setattr("src.main_app.db.services.settings_service.update_setting", lambda k, v, vt: False)

        request_form = {"setting_test_key": "new_val"}

        failed, deleted = settings_update_form(request_form)

        assert failed == ["test_key"]
        assert deleted == []

    def test_skips_when_form_key_not_in_request_form(self, monkeypatch):
        mock_settings = [
            {"key": "test_key", "value_type": "string", "value": "val"},
        ]
        monkeypatch.setattr("src.main_app.db.services.settings_service.get_all_settings_raw", lambda: mock_settings)

        update_called = []

        def mock_update(key, value, v_type):
            update_called.append(key)
            return True

        monkeypatch.setattr("src.main_app.db.services.settings_service.update_setting", mock_update)

        request_form = {"other_key": "value"}

        failed, deleted = settings_update_form(request_form)

        assert failed == []
        assert deleted == []
        assert update_called == []
