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
