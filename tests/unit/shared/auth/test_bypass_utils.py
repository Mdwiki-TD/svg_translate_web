"""Unit tests for bypass_utils.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.main_app.shared.auth.bypass_utils import is_coordinator_bypass_enabled


def test_bypass_enabled_in_development():
    mock_app = MagicMock()
    mock_app.config = {"ENV": "development", "UI_TEST_BYPASS_COORDINATOR_CHECK": True}
    with patch("src.main_app.shared.auth.bypass_utils.current_app", mock_app):
        assert is_coordinator_bypass_enabled() is True


def test_bypass_ignored_in_production():
    mock_app = MagicMock()
    mock_app.config = {"ENV": "production", "UI_TEST_BYPASS_COORDINATOR_CHECK": True}
    with patch("src.main_app.shared.auth.bypass_utils.current_app", mock_app):
        assert is_coordinator_bypass_enabled() is False


def test_bypass_disabled_in_development():
    mock_app = MagicMock()
    mock_app.config = {"ENV": "development", "UI_TEST_BYPASS_COORDINATOR_CHECK": False}
    with patch("src.main_app.shared.auth.bypass_utils.current_app", mock_app):
        assert is_coordinator_bypass_enabled() is False
