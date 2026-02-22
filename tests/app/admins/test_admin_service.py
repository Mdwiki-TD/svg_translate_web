from unittest.mock import MagicMock, patch

import pytest

from src.main_app.admins.admin_service import (
    _ADMINS_STORE,
    active_coordinators,
    add_coordinator,
    delete_coordinator,
    get_admins_db,
    list_coordinators,
    set_coordinator_active,
)
from src.main_app.config import DbConfig


@patch("src.main_app.admins.admin_service.CoordinatorsDB")
@patch("src.main_app.admins.admin_service.has_db_config")
def test_get_admins_db_first_call(mock_has_db_config, mock_coordinators_db):
    """Test get_admins_db creates a new instance on first call."""
    # Reset the global variable
    import src.main_app.admins.admin_service

    src.main_app.admins.admin_service._ADMINS_STORE = None

    mock_has_db_config.return_value = True
    mock_db_instance = MagicMock()
    mock_coordinators_db.return_value = mock_db_instance

    # Mock settings.database_data
    with patch("src.main_app.admins.admin_service.settings") as mock_settings:
        mock_settings.database_data = DbConfig(
            **{"db_host": "localhost", "db_name": "test", "db_user": "user", "db_password": "pass"}
        )

        result = get_admins_db()

        assert result == mock_db_instance
        mock_coordinators_db.assert_called_once()
        assert src.main_app.admins.admin_service._ADMINS_STORE == mock_db_instance


@patch("src.main_app.admins.admin_service.CoordinatorsDB")
@patch("src.main_app.admins.admin_service.has_db_config")
def test_get_admins_db_cached(mock_has_db_config, mock_coordinators_db):
    """Test get_admins_db returns cached instance on subsequent calls."""
    # Reset the global variable
    import src.main_app.admins.admin_service

    mock_cached_db = MagicMock()
    src.main_app.admins.admin_service._ADMINS_STORE = mock_cached_db

    result = get_admins_db()

    assert result == mock_cached_db
    mock_coordinators_db.assert_not_called()


@patch("src.main_app.admins.admin_service.has_db_config")
def test_get_admins_db_no_config(mock_has_db_config):
    """Test get_admins_db raises RuntimeError when no DB config."""
    # Reset the global variable to ensure it's None
    import src.main_app.admins.admin_service

    src.main_app.admins.admin_service._ADMINS_STORE = None

    mock_has_db_config.return_value = False

    with pytest.raises(RuntimeError, match="Coordinator administration requires database configuration"):
        get_admins_db()


@patch("src.main_app.admins.admin_service.get_admins_db")
def test_active_coordinators(mock_get_admins_db):
    """Test active_coordinators function."""
    mock_store = MagicMock()
    mock_get_admins_db.return_value = mock_store

    # Mock coordinator records
    mock_coord1 = MagicMock()
    mock_coord1.username = "user1"
    mock_coord1.is_active = True

    mock_coord2 = MagicMock()
    mock_coord2.username = "user2"
    mock_coord2.is_active = False

    mock_coord3 = MagicMock()
    mock_coord3.username = "user3"
    mock_coord3.is_active = True

    mock_store.list.return_value = [mock_coord1, mock_coord2, mock_coord3]

    result = active_coordinators()

    assert result == ["user1", "user3"]  # Only active coordinators
    mock_store.list.assert_called_once()


@patch("src.main_app.admins.admin_service.get_admins_db")
def test_list_coordinators(mock_get_admins_db):
    """Test list_coordinators function."""
    mock_store = MagicMock()
    mock_get_admins_db.return_value = mock_store

    mock_records = [MagicMock(), MagicMock()]
    mock_store.list.return_value = mock_records

    result = list_coordinators()

    assert result == mock_records
    mock_store.list.assert_called_once()


@patch("src.main_app.admins.admin_service.get_admins_db")
def test_add_coordinator(mock_get_admins_db):
    """Test add_coordinator function."""
    mock_store = MagicMock()
    mock_get_admins_db.return_value = mock_store

    mock_record = MagicMock()
    mock_store.add.return_value = mock_record

    result = add_coordinator("new_user")

    assert result == mock_record
    mock_store.add.assert_called_once_with("new_user")


@patch("src.main_app.admins.admin_service.get_admins_db")
def test_set_coordinator_active(mock_get_admins_db):
    """Test set_coordinator_active function."""
    mock_store = MagicMock()
    mock_get_admins_db.return_value = mock_store

    mock_record = MagicMock()
    mock_store.set_active.return_value = mock_record

    result = set_coordinator_active(123, True)

    assert result == mock_record
    mock_store.set_active.assert_called_once_with(123, True)


@patch("src.main_app.admins.admin_service.get_admins_db")
def test_delete_coordinator(mock_get_admins_db):
    """Test delete_coordinator function."""
    mock_store = MagicMock()
    mock_get_admins_db.return_value = mock_store

    mock_record = MagicMock()
    mock_store.delete.return_value = mock_record

    result = delete_coordinator(123)

    assert result == mock_record
    mock_store.delete.assert_called_once_with(123)
