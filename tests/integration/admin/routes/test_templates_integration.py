from unittest.mock import patch

from src.main_app.admin.routes.templates import (
    TemplatesRoutesFuncs,
)
from src.main_app.database.services import TemplateService


@patch("src.main_app.admin.routes.templates.flash")
@patch("src.main_app.admin.routes.templates.redirect")
@patch("src.main_app.admin.routes.templates.url_for")
def test_add_template_success(mock_url, mock_redirect, mock_flash, mock_app):
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    resp = TemplatesRoutesFuncs()._add_template({"title": "NewT", "main_file": "f.svg"})
    assert resp == "redirected"

    mock_flash.assert_called_with("Template 'NewT' added.", "success")

    svc = TemplateService()
    record = svc.get_template_by_title("NewT")
    assert record is not None
    assert record.main_file == "f.svg"


@patch("src.main_app.admin.routes.templates.flash")
@patch("src.main_app.admin.routes.templates.redirect")
@patch("src.main_app.admin.routes.templates.url_for")
def test_add_template_missing_title(mock_url, mock_redirect, mock_flash, mock_app):
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    resp = TemplatesRoutesFuncs()._add_template({"title": ""})
    assert resp == "redirected"
    mock_flash.assert_called_with("Title is required to add a template.", "danger")


@patch("src.main_app.admin.routes.templates.flash")
@patch("src.main_app.admin.routes.templates.redirect")
@patch("src.main_app.admin.routes.templates.url_for")
def test_update_template_success(mock_url, mock_redirect, mock_flash, mock_app):
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    svc = TemplateService()
    created = svc.add_template_data({"title": "UpdT", "main_file": "f.svg"})
    assert created is not None

    resp = TemplatesRoutesFuncs()._update_template({"id": created.id, "title": "UpdT", "main_file": "f2.svg"})
    assert resp == "redirected"

    mock_flash.assert_called_with("Template 'UpdT' main file: f2.svg updated.", "success")

    updated = svc.get_template(created.id)
    assert updated is not None
    assert updated.main_file == "f2.svg"


@patch("src.main_app.admin.routes.templates.flash")
@patch("src.main_app.admin.routes.templates.redirect")
@patch("src.main_app.admin.routes.templates.url_for")
def test_update_template_missing_id(mock_url, mock_redirect, mock_flash, mock_app):
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    resp = TemplatesRoutesFuncs()._update_template({"title": "UpdT"})
    assert resp == "redirected"
    mock_flash.assert_called_with("Template ID is required to update a template.", "danger")


@patch("src.main_app.admin.routes.templates.flash")
@patch("src.main_app.admin.routes.templates.redirect")
@patch("src.main_app.admin.routes.templates.url_for")
def test_delete_template_success(mock_url, mock_redirect, mock_flash, mock_app):
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    svc = TemplateService()
    created = svc.add_template_data({"title": "DelT", "main_file": "f.svg"})
    assert created is not None

    resp = TemplatesRoutesFuncs()._delete_template(created.id, False)
    assert resp == "redirected"

    mock_flash.assert_called_with("Template 'DelT' removed.", "success")

    assert svc.get_template(created.id) is None


def test_create_json_file_success(mock_app):
    """Test create_json_file returns JSON file with templates data."""
    from src.main_app.admin.routes.templates import create_json_file

    svc = TemplateService()
    svc.add_template_data(
        {
            "title": "Test Template",
            "main_file": "Example.svg",
            "last_world_file": "World.svg",
            "source": "Test source",
        }
    )

    with mock_app.app_context():
        response, status_code = create_json_file()

    assert status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert "attachment" in response.headers["Content-Disposition"]
    assert "templates.json" in response.headers["Content-Disposition"]


def test_create_json_file_no_templates(mock_app):
    """Test create_json_file returns 404 when no templates."""
    from src.main_app.admin.routes.templates import create_json_file

    msg, status_code = create_json_file()

    assert status_code == 404
    assert "No templates found" in msg


def test_edit_template_found(mock_app):
    """Test TemplatesRoutesFuncs().edit_template returns template when found."""
    svc = TemplateService()
    created = svc.add_template_data(
        {
            "title": "Test Template",
            "main_file": "Example.svg",
        }
    )
    assert created is not None

    with mock_app.test_request_context():
        with patch("src.main_app.admin.routes.templates.render_template") as mock_render:
            mock_render.return_value = "rendered"
            result = TemplatesRoutesFuncs().edit_template(created.id)
            assert result == "rendered"
            mock_render.assert_called_once()
            kwargs = mock_render.call_args[1]
            assert kwargs["template"].id == created.id
            assert kwargs["template"].title == "Test Template"
            assert kwargs["error"] is None


def test_edit_template_not_found(mock_app):
    """Test TemplatesRoutesFuncs().edit_template returns error when template not found."""
    with mock_app.test_request_context():
        with patch("src.main_app.admin.routes.templates.render_template") as mock_render:
            mock_render.return_value = "rendered"
            result = TemplatesRoutesFuncs().edit_template(999)
            assert result == "rendered"
            mock_render.assert_called_once()
            kwargs = mock_render.call_args[1]
            assert kwargs["template"] is None
            assert "not found" in kwargs["error"].lower()
