"""Unit tests for coordinators exception handling improvements."""

from __future__ import annotations

import logging
from unittest.mock import Mock

from src.main_app.app_routes.admin.admin_routes import coordinators


def test_add_coordinator_catches_both_lookup_and_value_errors(monkeypatch, caplog):
    """Test that _add_coordinator catches both LookupError and ValueError in single except clause."""
    mock_service = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin.admin_routes.coordinators.admin_service", mock_service)

    # Mock Flask globals to avoid "Working outside of request context" errors
    mock_request = Mock()
    mock_request.form.get.return_value = "test_user"
    monkeypatch.setattr("src.main_app.app_routes.admin.admin_routes.coordinators.request", mock_request)

    mock_flash = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin.admin_routes.coordinators.flash", mock_flash)

    mock_redirect = Mock()
    monkeypatch.setattr("src.main_app.app_routes.admin.admin_routes.coordinators.redirect", mock_redirect)

    monkeypatch.setattr("src.main_app.app_routes.admin.admin_routes.coordinators.url_for", lambda x: f"/{x}")

    # Test with ValueError
    mock_service.add_coordinator = Mock(side_effect=ValueError("Username invalid"))

    with caplog.at_level(logging.ERROR):
        coordinators._add_coordinator()

    # Verify exception was logged
    assert "Unable to Add coordinator" in caplog.text

    # Verify flash was called with the error message
    mock_flash.assert_called_once_with("Username invalid", "warning")

    # Reset for next part
    mock_flash.reset_mock()
    caplog.clear()

    # Test with LookupError
    mock_service.add_coordinator = Mock(side_effect=LookupError("User not found"))

    with caplog.at_level(logging.ERROR):
        coordinators._add_coordinator()

    mock_flash.assert_called_once_with("User not found", "warning")


def test_logger_uses_svg_translate_name():
    """Test that the logger uses 'svg_translate' instead of __name__."""
    assert coordinators.logger.name == "svg_translate"
