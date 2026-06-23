# ruff: noqa: F401
"""
Unit tests for src/main_app/db/services/admin_service.py.
TODO: write tests
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.db.services.admin_service import (
    add_coordinator,
    get_coordinator_by_id,
    is_active_coordinator,
    list_coordinators,
    set_coordinator_active,
)
from src.main_app.db.services.delete_service import delete_coordinator


class TestAddCoordinator:
    def test_empty_username_raises(self):
        with patch("src.main_app.db.services.admin_service.db"):
            with pytest.raises(ValueError, match="Username is required"):
                add_coordinator("")


class TestGetCoordinatorById:
    def test_not_found_raises(self):
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        with patch("src.main_app.db.services.admin_service.db", mock_db):
            with pytest.raises(LookupError, match="not found"):
                get_coordinator_by_id(999)


class TestIsActiveCoordinatorBypass:
    def test_bypass_enabled_in_development(self):
        mock_app = MagicMock()
        mock_app.config = {"ENV": "development", "UI_TEST_BYPASS_COORDINATOR_CHECK": True}
        with patch("src.main_app.db.services.admin_service.current_app", mock_app):
            assert is_active_coordinator("any_user") is True

    def test_bypass_ignored_in_production(self):
        mock_app = MagicMock()
        mock_app.config = {"ENV": "production", "UI_TEST_BYPASS_COORDINATOR_CHECK": True}
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        with (
            patch("src.main_app.db.services.admin_service.current_app", mock_app),
            patch("src.main_app.db.services.admin_service.db", mock_db),
        ):
            assert is_active_coordinator("any_user") is False
            # Verify it actually queried the DB
            assert mock_db.session.query.called

    def test_bypass_disabled_in_development(self):
        mock_app = MagicMock()
        mock_app.config = {"ENV": "development", "UI_TEST_BYPASS_COORDINATOR_CHECK": False}
        mock_db = MagicMock()
        mock_db.session.query.return_value.filter.return_value.first.return_value = None
        with (
            patch("src.main_app.db.services.admin_service.current_app", mock_app),
            patch("src.main_app.db.services.admin_service.db", mock_db),
        ):
            assert is_active_coordinator("any_user") is False
            # Verify it actually queried the DB
            assert mock_db.session.query.called
