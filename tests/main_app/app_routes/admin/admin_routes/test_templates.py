from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.main_app.app_routes.admin.admin_routes.templates import (
    Templates,
    _add_template,
    _delete_template,
    _templates_dashboard,
    _update_template,
)


@pytest.fixture
def app():
    app = Flask(__name__)
    app.secret_key = "test"
    return app


@patch("src.main_app.app_routes.admin.admin_routes.templates.render_template")
@patch("src.main_app.app_routes.admin.admin_routes.templates.template_service")
@patch("src.main_app.app_routes.admin.admin_routes.templates.current_user")
def test_templates_dashboard(mock_current_user, mock_service, mock_render, app):
    mock_service.list_templates.return_value = ["t1", "t2"]
    mock_current_user.return_value = "user"
    mock_render.return_value = "rendered"

    with app.test_request_context():
        resp = _templates_dashboard()
        assert resp == "rendered"

        mock_render.assert_called_once()
        kwargs = mock_render.call_args[1]
        assert kwargs["templates"] == ["t1", "t2"]
        assert kwargs["total_templates"] == 2
        assert kwargs["current_user"] == "user"


@patch("src.main_app.app_routes.admin.admin_routes.templates.template_service")
@patch("src.main_app.app_routes.admin.admin_routes.templates.flash")
@patch("src.main_app.app_routes.admin.admin_routes.templates.redirect")
@patch("src.main_app.app_routes.admin.admin_routes.templates.url_for")
def test_add_template_success(mock_url, mock_redirect, mock_flash, mock_service, app):
    mock_service.add_template.return_value = MagicMock(title="NewT")
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with app.test_request_context(method="POST", data={"title": "NewT", "main_file": "f.svg"}):
        resp = _add_template()
        assert resp == "redirected"

        mock_service.add_template.assert_called_with("NewT", "f.svg", "")
        mock_flash.assert_called_with("Template 'NewT' added.", "success")


@patch("src.main_app.app_routes.admin.admin_routes.templates.flash")
@patch("src.main_app.app_routes.admin.admin_routes.templates.redirect")
@patch("src.main_app.app_routes.admin.admin_routes.templates.url_for")
def test_add_template_missing_title(mock_url, mock_redirect, mock_flash, app):
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with app.test_request_context(method="POST", data={"title": ""}):
        resp = _add_template()
        assert resp == "redirected"
        mock_flash.assert_called_with("Title is required to add a template.", "danger")


@patch("src.main_app.app_routes.admin.admin_routes.templates.template_service")
@patch("src.main_app.app_routes.admin.admin_routes.templates.flash")
@patch("src.main_app.app_routes.admin.admin_routes.templates.redirect")
@patch("src.main_app.app_routes.admin.admin_routes.templates.url_for")
def test_update_template_success(mock_url, mock_redirect, mock_flash, mock_service, app):
    mock_service.update_template.return_value = MagicMock(title="UpdT")
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with app.test_request_context(method="POST", data={"id": 1, "title": "UpdT", "main_file": "f2.svg"}):
        resp = _update_template()
        assert resp == "redirected"

        mock_service.update_template.assert_called_with(1, "UpdT", "f2.svg", "")
        mock_flash.assert_called_with("Template 'UpdT' main file: f2.svg updated.", "success")


@patch("src.main_app.app_routes.admin.admin_routes.templates.flash")
@patch("src.main_app.app_routes.admin.admin_routes.templates.redirect")
@patch("src.main_app.app_routes.admin.admin_routes.templates.url_for")
def test_update_template_missing_id(mock_url, mock_redirect, mock_flash, app):
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with app.test_request_context(method="POST", data={"title": "UpdT"}):
        resp = _update_template()
        assert resp == "redirected"
        mock_flash.assert_called_with("Template ID is required to update a template.", "danger")


@patch("src.main_app.app_routes.admin.admin_routes.templates.template_service")
@patch("src.main_app.app_routes.admin.admin_routes.templates.flash")
@patch("src.main_app.app_routes.admin.admin_routes.templates.redirect")
@patch("src.main_app.app_routes.admin.admin_routes.templates.url_for")
def test_delete_template_success(mock_url, mock_redirect, mock_flash, mock_service, app):
    mock_service.delete_template.return_value = MagicMock(title="DelT")
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with app.test_request_context():
        resp = _delete_template(1)
        assert resp == "redirected"

        mock_service.delete_template.assert_called_with(1)
        mock_flash.assert_called_with("Template 'DelT' removed.", "success")


def test_Templates():
    # Verify routes registration
    bp = MagicMock()
    Templates(bp)

    # Should register 2 GET routes, 3 POST routes
    assert bp.get.call_count == 2
    assert bp.post.call_count == 3

    # Check endpoints
    bp.get.assert_any_call("/templates")
    bp.get.assert_any_call("/templates/<int:template_id>/edit")
    bp.post.assert_any_call("/templates/add")
    bp.post.assert_any_call("/templates/update")
    bp.post.assert_any_call("/templates/<int:template_id>/delete")
