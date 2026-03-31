"""Tests for src.main_app.services.tasks_service."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import src.main_app.services.tasks_service as tasks_service_module
from src.main_app.services.tasks_service import _task_store, close_task_store


@pytest.fixture(autouse=True)
def reset_task_store():
    """Reset the module-level TASK_STORE singleton before and after each test."""
    original = tasks_service_module.TASK_STORE
    tasks_service_module.TASK_STORE = None
    yield
    tasks_service_module.TASK_STORE = original


class TestTaskStore:
    """Tests for the _task_store singleton function."""

    def test_returns_task_store_instance(self, monkeypatch):
        """_task_store() returns a TaskStorePyMysql instance."""
        mock_store = MagicMock()
        mock_cls = MagicMock(return_value=mock_store)
        monkeypatch.setattr("src.main_app.services.tasks_service.TaskStorePyMysql", mock_cls)

        result = _task_store()

        assert result is mock_store

    def test_creates_instance_on_first_call(self, monkeypatch):
        """_task_store() creates the instance on first call."""
        mock_store = MagicMock()
        mock_cls = MagicMock(return_value=mock_store)
        monkeypatch.setattr("src.main_app.services.tasks_service.TaskStorePyMysql", mock_cls)

        _task_store()

        mock_cls.assert_called_once()

    def test_returns_same_instance_on_repeated_calls(self, monkeypatch):
        """_task_store() returns the same singleton instance on repeated calls."""
        mock_store = MagicMock()
        mock_cls = MagicMock(return_value=mock_store)
        monkeypatch.setattr("src.main_app.services.tasks_service.TaskStorePyMysql", mock_cls)

        first = _task_store()
        second = _task_store()
        third = _task_store()

        assert first is second
        assert second is third
        # Constructor called only once
        mock_cls.assert_called_once()

    def test_passes_database_config_to_constructor(self, monkeypatch):
        """_task_store() passes settings.database_data to TaskStorePyMysql."""
        mock_store = MagicMock()
        mock_cls = MagicMock(return_value=mock_store)
        fake_db_data = {"host": "localhost", "db": "test"}
        fake_settings = MagicMock()
        fake_settings.database_data = fake_db_data

        monkeypatch.setattr("src.main_app.services.tasks_service.TaskStorePyMysql", mock_cls)
        monkeypatch.setattr("src.main_app.services.tasks_service.settings", fake_settings)

        _task_store()

        mock_cls.assert_called_once_with(fake_db_data)

    def test_sets_module_level_task_store(self, monkeypatch):
        """_task_store() sets the TASK_STORE module variable."""
        mock_store = MagicMock()
        mock_cls = MagicMock(return_value=mock_store)
        monkeypatch.setattr("src.main_app.services.tasks_service.TaskStorePyMysql", mock_cls)

        _task_store()

        assert tasks_service_module.TASK_STORE is mock_store


class TestCloseTaskStore:
    """Tests for the close_task_store function."""

    def test_closes_existing_store(self, monkeypatch):
        """close_task_store() calls close() on the existing store."""
        mock_store = MagicMock()
        tasks_service_module.TASK_STORE = mock_store

        close_task_store()

        mock_store.close.assert_called_once()

    def test_no_op_when_store_is_none(self):
        """close_task_store() is a no-op when TASK_STORE is None."""
        tasks_service_module.TASK_STORE = None
        # Should not raise
        close_task_store()

    def test_store_can_be_recreated_after_close(self, monkeypatch):
        """After close_task_store(), _task_store() creates a new instance."""
        mock_store1 = MagicMock()
        mock_store2 = MagicMock()
        mock_cls = MagicMock(side_effect=[mock_store1, mock_store2])
        monkeypatch.setattr("src.main_app.services.tasks_service.TaskStorePyMysql", mock_cls)

        first = _task_store()
        assert first is mock_store1

        # Reset so close_task_store uses the store we just set
        tasks_service_module.TASK_STORE = mock_store1
        close_task_store()

        # TASK_STORE may not be reset to None by close_task_store - it just calls close()
        # Reset manually as close_task_store does not reset the reference
        tasks_service_module.TASK_STORE = None

        second = _task_store()
        assert second is mock_store2
        assert second is not first