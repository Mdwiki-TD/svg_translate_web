"""Unit tests for templates admin routes improvements."""

from __future__ import annotations

from unittest.mock import Mock

from src.main_app.admin.routes import templates


def test_update_template_uses_request_form_type_parameter(mock_app, monkeypatch):
    """Test that _update_template uses request.form.get with type=int parameter."""
    with mock_app.test_request_context(
        method="POST", data={"id": "42", "title": "Test Title", "main_file": "test.svg"}
    ):
        mock_update_template = Mock(return_value=Mock(title="Test Title"))

        monkeypatch.setattr("src.main_app.admin.routes.templates.update_template_data", mock_update_template)
        monkeypatch.setattr("src.main_app.admin.routes.templates.flash", Mock())
        monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", Mock())
        monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", Mock())

        # Spy on request.form.get with wraps to preserve original behavior
        original_get = templates.request.form.get
        mock_get = Mock(wraps=original_get)
        monkeypatch.setattr(templates.request.form, "get", mock_get)

        templates._update_template()

        # Verify get was called with type parameter for id
        mock_get.assert_any_call("id", default=0, type=int)


def test_update_template_correct_error_message_for_missing_title(mock_app, monkeypatch):
    """Test that _update_template shows correct error message for update (not 'add')."""
    with mock_app.test_request_context(method="POST", data={"id": "1", "title": "", "main_file": "test.svg"}):
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.templates.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", Mock())
        monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", Mock())

        templates._update_template()

    # Verify the correct error message (should say "update" not "add")
    mock_flash.assert_called_once()
    flash_message = mock_flash.call_args[0][0]
    assert "update" in flash_message.lower()
    assert "Title is required to update a template" in flash_message


def test_update_template_missing_id_shows_error(mock_app, monkeypatch):
    """Test that _update_template shows error when template ID is missing."""
    with mock_app.test_request_context(method="POST", data={"id": "0", "title": "Test", "main_file": "test.svg"}):
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.templates.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", Mock())
        monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", Mock())

        templates._update_template()

    mock_flash.assert_called_once_with("Template ID is required to update a template.", "danger")
