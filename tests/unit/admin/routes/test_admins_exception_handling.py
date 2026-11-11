"""Unit tests for admins exception handling improvements."""

from __future__ import annotations

import logging
from unittest.mock import Mock

import pytest
from src.main_app.admin.routes.admins import AddAdminView


class TestAddAdminExceptionHandling:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = AddAdminView()

    def test_catches_both_lookup_and_value_errors(self, monkeypatch, caplog):
        """Test that add catches both LookupError and ValueError in single except clause."""
        mock_add_admin = Mock()
        monkeypatch.setattr(self.service.service, "add_admin", mock_add_admin)

        # Mock Flask globals to avoid "Working outside of request context" errors
        mock_req = Mock()
        mock_req.form.get.return_value = "test_user"
        monkeypatch.setattr("src.main_app.admin.routes.admins.request", mock_req)

        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.admins.flash", mock_flash)

        mock_redirect = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.admins.redirect", mock_redirect)

        monkeypatch.setattr("src.main_app.admin.routes.admins.url_for", lambda x: f"/{x}")

        # Test with ValueError
        mock_add_admin.side_effect = ValueError("Username invalid")

        with caplog.at_level(logging.ERROR):
            self.service.post()

        # Verify exception was logged
        assert "Unable to Add admin" in caplog.text

        # Verify flash was called with the error message
        mock_flash.assert_called_once_with("Unable to add 'test_user' as admin", "warning")

        # Reset for next part
        mock_flash.reset_mock()
        caplog.clear()

        # Test with LookupError
        mock_add_admin.side_effect = LookupError("User not found")

        with caplog.at_level(logging.ERROR):
            self.service.post()

        mock_flash.assert_called_once_with("Unable to add 'test_user' as admin", "warning")
