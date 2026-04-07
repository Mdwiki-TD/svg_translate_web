"""Unit tests for templates admin routes improvements."""

from __future__ import annotations

from unittest.mock import Mock, patch

from src.main_app.app_routes.admin_routes import templates


def test_update_template_uses_request_form_type_parameter(app_mock):
    """Test that _update_template uses request.form.get with type=int parameter."""
    with app_mock.test_request_context(
        method="POST", data={"id": "42", "title": "Test Title", "main_file": "test.svg"}
    ):
        mock_service = Mock()
        mock_service.update_template = Mock(return_value=Mock(title="Test Title"))

        with patch("src.main_app.app_routes.admin_routes.templates.template_service", mock_service):
            with patch("src.main_app.app_routes.admin_routes.templates.flash"):
                with patch("src.main_app.app_routes.admin_routes.templates.redirect"):
                    with patch("src.main_app.app_routes.admin_routes.templates.url_for"):
                        # We want to spy on request.form.get
                        with patch.object(templates.request.form, "get", wraps=templates.request.form.get) as mock_get:
                            templates._update_template()

                            # Verify get was called with type parameter for id
                            mock_get.assert_any_call("id", default=0, type=int)


def test_update_template_correct_error_message_for_missing_title(app_mock):
    """Test that _update_template shows correct error message for update (not 'add')."""
    with app_mock.test_request_context(method="POST", data={"id": "1", "title": "", "main_file": "test.svg"}):
        with patch("src.main_app.app_routes.admin_routes.templates.flash") as mock_flash:
            with patch("src.main_app.app_routes.admin_routes.templates.redirect"):
                with patch("src.main_app.app_routes.admin_routes.templates.url_for"):
                    templates._update_template()

        # Verify the correct error message (should say "update" not "add")
        mock_flash.assert_called_once()
        flash_message = mock_flash.call_args[0][0]
        assert "update" in flash_message.lower()
        assert "Title is required to update a template" in flash_message


def test_update_template_missing_id_shows_error(app_mock):
    """Test that _update_template shows error when template ID is missing."""
    with app_mock.test_request_context(method="POST", data={"id": "0", "title": "Test", "main_file": "test.svg"}):
        with patch("src.main_app.app_routes.admin_routes.templates.flash") as mock_flash:
            with patch("src.main_app.app_routes.admin_routes.templates.redirect"):
                with patch("src.main_app.app_routes.admin_routes.templates.url_for"):
                    templates._update_template()

        mock_flash.assert_called_once_with("Template ID is required to update a template.", "danger")
