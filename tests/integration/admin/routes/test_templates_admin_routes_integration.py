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
    """Test that _update_template uses request.form.get with type=int parameter."""
    mock_services["update_template_data"].return_value = Mock(title="Test Title")

    with mock_app.test_request_context(
        method="POST", data={"id": "42", "title": "Test Title", "main_file": "test.svg"}
    ):
        # Spy on request.form.get with wraps to preserve original behavior
        original_get = templates.request.form.get
        mock_get = Mock(wraps=original_get)
        monkeypatch.setattr(templates.request.form, "get", mock_get)

        templates.TemplatesRoutesFuncs().update_template()

        # Verify get was called with type parameter for id
        mock_get.assert_any_call("id", default=0, type=int)


def test_update_template_correct_error_message_for_missing_title(mock_app, mock_services):
    """Test that _update_template shows correct error message for update (not 'add')."""
    with mock_app.test_request_context(method="POST", data={"id": "1", "title": "", "main_file": "test.svg"}):
        templates.TemplatesRoutesFuncs().update_template()

    # Verify the correct error message (should say "update" not "add")
    mock_services["flash"].assert_called_once()
    flash_message = mock_services["flash"].call_args[0][0]
    assert "update" in flash_message.lower()
    assert "Title is required to update a template" in flash_message


def test_update_template_missing_id_shows_error(mock_app, mock_services):
    """Test that _update_template shows error when template ID is missing."""
    with mock_app.test_request_context(method="POST", data={"id": "0", "title": "Test", "main_file": "test.svg"}):
        templates.TemplatesRoutesFuncs().update_template()

    mock_services["flash"].assert_called_once_with("Template ID is required to update a template.", "danger")
