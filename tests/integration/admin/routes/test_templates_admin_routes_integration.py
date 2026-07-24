"""Unit tests for templates admin routes improvements."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.main_app.admin.routes import templates


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    """Mock template admin route dependencies."""
    mocks = {
        "update_template_data": Mock(),
        "flash": Mock(),
        "redirect": Mock(),
        "url_for": Mock(),
    }
    monkeypatch.setattr(
        "src.main_app.admin.routes.templates.TemplateService.update_template_data", mocks["update_template_data"]
    )
    monkeypatch.setattr("src.main_app.admin.routes.templates.flash", mocks["flash"])
    monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", mocks["redirect"])
    monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", mocks["url_for"])
    return mocks


def test_update_template_uses_request_form_type_parameter(mock_app, mock_services, monkeypatch):
    """Test that _update_template parses id as int (type=int parameter)."""
    mock_services["update_template_data"].return_value = Mock(title="Test Title")

    templates.TemplatesRoutesFuncs()._update_template({"id": "42", "title": "Test Title", "main_file": "test.svg"})

    mock_services["update_template_data"].assert_called_once()
    call_args = mock_services["update_template_data"].call_args[0]
    assert call_args[0] == 42
    assert isinstance(call_args[0], int)


def test_update_template_correct_error_message_for_missing_title(mock_app, mock_services):
    """Test that _update_template shows correct error message for update (not 'add')."""
    templates.TemplatesRoutesFuncs()._update_template({"id": "1", "title": "", "main_file": "test.svg"})

    # Verify the correct error message (should say "update" not "add")
    mock_services["flash"].assert_called_once()
    flash_message = mock_services["flash"].call_args[0][0]
    assert "update" in flash_message.lower()
    assert "Title is required to update a template" in flash_message


def test_update_template_missing_id_shows_error(mock_app, mock_services):
    """Test that _update_template shows error when template ID is missing."""
    templates.TemplatesRoutesFuncs()._update_template({"id": "0", "title": "Test", "main_file": "test.svg"})

    mock_services["flash"].assert_called_once_with("Template ID is required to update a template.", "danger")
