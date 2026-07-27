from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.db.services.settings_service import SettingsService, _serialize_value


@pytest.fixture
def mock_db_session(monkeypatch: pytest.MonkeyPatch):
    mock_session = MagicMock()
    monkeypatch.setattr("src.main_app.extensions.db.session", mock_session)
    return mock_session


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self, mock_db_session):
        self.service = SettingsService()


class TestListSettingsReady:

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        self.service = SettingsService()
        monkeypatch.setattr(self.service.session, "rollback", MagicMock())

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

    def test_list_settings(self):
        mock_records = [MagicMock(), MagicMock()]
        self.service.session.query.return_value.all.return_value = mock_records

        result = self.service.list_settings()
        assert result == mock_records


class TestGetAllSettingsRaw(TestSetup):
    """Tests for get_all_settings_raw."""

    def test_returns_to_dict_of_all_settings(self):
        mock_record1 = MagicMock()
        mock_record1.to_dict.return_value = {"key": "setting1", "value": "val1"}
        mock_record2 = MagicMock()
        mock_record2.to_dict.return_value = {"key": "setting2", "value": "val2"}
        self.service.list_settings = MagicMock()
        self.service.list_settings.return_value = [mock_record1, mock_record2]
        result = self.service.get_all_settings_raw()
        assert result == [{"key": "setting1", "value": "val1"}, {"key": "setting2", "value": "val2"}]


class TestGetAllSettingsReady(TestSetup):
    """Tests for get_all_settings_ready parsing logic."""

    def test_boolean_true(self):
        mock_record = MagicMock()
        mock_record.value_type = "boolean"
        mock_record.value = "true"
        mock_record.key = "test_bool"
        self.service.list_settings = MagicMock()
        self.service.list_settings.return_value = [mock_record]
        assert self.service.get_all_settings_ready() == {"test_bool": True}

    def test_boolean_false(self):
        mock_record = MagicMock()
        mock_record.value_type = "boolean"
        mock_record.value = "false"
        mock_record.key = "test_bool"
        self.service.list_settings = MagicMock()
        self.service.list_settings.return_value = [mock_record]
        assert self.service.get_all_settings_ready() == {"test_bool": False}

    def test_integer_from_string(self):
        mock_record = MagicMock()
        mock_record.value_type = "integer"
        mock_record.value = "42"
        mock_record.key = "test_int"
        self.service.list_settings = MagicMock()
        self.service.list_settings.return_value = [mock_record]
        assert self.service.get_all_settings_ready() == {"test_int": 42}

    def test_integer_from_int(self):
        mock_record = MagicMock()
        mock_record.value_type = "integer"
        mock_record.value = 42
        mock_record.key = "test_int"
        self.service.list_settings = MagicMock()
        self.service.list_settings.return_value = [mock_record]
        assert self.service.get_all_settings_ready() == {"test_int": 42}

    def test_integer_invalid(self, caplog):
        mock_record = MagicMock()
        mock_record.value_type = "integer"
        mock_record.value = "not_a_number"
        mock_record.key = "test_int"
        self.service.list_settings = MagicMock()
        self.service.list_settings.return_value = [mock_record]
        with caplog.at_level("WARNING"):
            result = self.service.get_all_settings_ready()
        assert result == {"test_int": None}
        assert "Could not parse setting test_int with value not_a_number" in caplog.text

    def test_string(self):
        mock_record = MagicMock()
        mock_record.value_type = "string"
        mock_record.value = "hello"
        mock_record.key = "test_str"
        self.service.list_settings = MagicMock()
        self.service.list_settings.return_value = [mock_record]
        assert self.service.get_all_settings_ready() == {"test_str": "hello"}

    def test_unknown_type_logs_warning(self, caplog):
        mock_record = MagicMock()
        mock_record.value_type = "unknown"
        mock_record.value = "anything"
        mock_record.key = "test_unknown"
        self.service.list_settings = MagicMock()
        self.service.list_settings.return_value = [mock_record]
        with caplog.at_level("WARNING"):
            result = self.service.get_all_settings_ready()
        assert result == {"test_unknown": None}
        assert "Could not parse setting test_unknown with value anything" in caplog.text


class TestGetSettingByKey(TestSetup):
    """Tests for get_setting_by_key."""

    def test_returns_setting_by_key(self):
        mock_setting = MagicMock()
        self.service.session.execute.return_value.scalars.return_value.first.return_value = mock_setting

        result = self.service.get_setting_by_key("test_key")
        assert result == mock_setting

    def test_returns_none_for_missing_key(self):
        self.service.session.execute.return_value.scalars.return_value.first.return_value = None
        result = self.service.get_setting_by_key("nonexistent")
        assert result is None


class TestUpdateSetting(TestSetup):
    """Tests for update_setting."""

    def test_updates_existing_setting(self):
        mock_setting = MagicMock()
        mock_setting.value = None
        mock_setting.title = "Original"
        mock_setting.value_type = "string"

        self.service.session.execute.return_value.scalars.return_value.first.return_value = mock_setting

        result = self.service.update_setting("test_key", "new_value", "string", "New Title")

        assert mock_setting.value == "new_value"
        assert mock_setting.title == "New Title"
        assert result is True

    def test_returns_false_when_not_found(self):
        self.service.session.execute.return_value.scalars.return_value.first.return_value = None

        result = self.service.update_setting("nonexistent", "value")
        assert result is False

    def test_serializes_value_according_to_type(self):
        mock_setting = MagicMock()
        mock_setting.value = None
        mock_setting.title = "Orig"
        mock_setting.value_type = "boolean"

        self.service.session.execute.return_value.scalars.return_value.first.return_value = mock_setting

        self.service.update_setting("test_key", True, "boolean")
        assert mock_setting.value == "true"

    def test_uses_existing_value_type_when_none_provided(self):
        mock_setting = MagicMock()
        mock_setting.value = None
        mock_setting.title = "Orig"
        mock_setting.value_type = "integer"

        self.service.session.execute.return_value.scalars.return_value.first.return_value = mock_setting

        self.service.update_setting("test_key", 99, value_type=None)
        assert mock_setting.value == "99"


class TestCreateSetting:

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        self.service = SettingsService()
        self._monkeypatch = monkeypatch

    """Tests for create_setting."""

    def test_creates_setting_successfully(self):
        added_settings: list = []

        self._monkeypatch.setattr(
            self.service.session,
            "add",
            lambda s: added_settings.append(s),
        )

        result = self.service.create_setting("test_key", "Test Title", "string", "test_value")

        assert result is True
        assert len(added_settings) == 1
        assert added_settings[0].key == "test_key"
        assert added_settings[0].title == "Test Title"
        assert added_settings[0].value == "test_value"
        assert added_settings[0].value_type == "string"

    def test_handles_exception_rollback(self):
        mock_rollback = MagicMock()
        self._monkeypatch.setattr(self.service.session, "rollback", mock_rollback)

        mock_commit = MagicMock()
        mock_commit.side_effect = Exception("DB error")
        self._monkeypatch.setattr(self.service.session, "commit", mock_commit)

        result = self.service.create_setting("test_key", "Test Title", "string", "test_value")

        assert result is False
        mock_rollback.assert_called_once()

    def test_default_value_boolean(self):
        added_settings: list = []

        self._monkeypatch.setattr(
            self.service.session,
            "add",
            lambda s: added_settings.append(s),
        )

        self.service.create_setting("bool_key", "Bool Setting", "boolean")
        assert added_settings[0].value == "false"

    def test_default_value_integer(self):
        added_settings: list = []

        self._monkeypatch.setattr(
            self.service.session,
            "add",
            lambda s: added_settings.append(s),
        )

        self.service.create_setting("int_key", "Int Setting", "integer")
        assert added_settings[0].value == "0"

    def test_default_value_string(self):
        added_settings: list = []

        self._monkeypatch.setattr(
            self.service.session,
            "add",
            lambda s: added_settings.append(s),
        )

        self.service.create_setting("str_key", "Str Setting", "string")
        assert added_settings[0].value == ""


class TestSerializeValue:
    """Test _serialize_value function."""

    def test_serialize_value_none(self):
        """Test _serialize_value handles None."""
        result = _serialize_value(None, "string")
        assert result is None

    def test_serialize_value_boolean(self):
        """Test _serialize_value handles booleans."""
        assert _serialize_value(True, "boolean") == "true"
        assert _serialize_value(False, "boolean") == "false"

    def test_serialize_value_integer(self):
        """Test _serialize_value handles integers."""
        assert _serialize_value(42, "integer") == "42"
        assert _serialize_value(-10, "integer") == "-10"

    def test_serialize_value_string(self):
        """Test _serialize_value handles strings."""
        assert _serialize_value("hello", "string") == "hello"
        assert _serialize_value(123, "string") == "123"
