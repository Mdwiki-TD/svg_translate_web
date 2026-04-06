from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from src.main_app.app_routes.admin_routes.templates import (
    Templates,
    _add_template,
    _delete_template,
    _templates_dashboard,
    _update_template,
)
from src.main_app.db import TemplateRecord


@pytest.fixture
def app_mock():
    app = Flask(__name__)
    app.secret_key = "test"
    return app


@patch("src.main_app.app_routes.admin_routes.templates.render_template")
@patch("src.main_app.app_routes.admin_routes.templates.template_service")
@patch("src.main_app.app_routes.admin_routes.templates.current_user")
def test_templates_dashboard(mock_current_user, mock_service, mock_render, app_mock):
    templates = [
        TemplateRecord(
            id=0,
            title="t1",
            main_file="",
            last_world_file="",
            created_at=None,
            updated_at=None,
            source=None,
        ),
        TemplateRecord(
            id=1,
            title="t2",
            main_file="",
            last_world_file="",
            created_at=None,
            updated_at=None,
            source=None,
        ),
    ]
    mock_service.list_templates.return_value = templates
    mock_current_user.return_value = "user"
    mock_render.return_value = "rendered"

    with app_mock.test_request_context():
        resp = _templates_dashboard()
        assert resp == "rendered"

        mock_render.assert_called_once()
        kwargs = mock_render.call_args[1]
        assert kwargs["templates"] == templates
        assert kwargs["total_templates"] == 2
        assert kwargs["current_user"] == "user"


@patch("src.main_app.app_routes.admin_routes.templates.template_service")
@patch("src.main_app.app_routes.admin_routes.templates.flash")
@patch("src.main_app.app_routes.admin_routes.templates.redirect")
@patch("src.main_app.app_routes.admin_routes.templates.url_for")
def test_add_template_success(mock_url, mock_redirect, mock_flash, mock_service, app_mock):
    mock_service.add_template_data.return_value = MagicMock(title="NewT")
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with app_mock.test_request_context(method="POST", data={"title": "NewT", "main_file": "f.svg"}):
        resp = _add_template()
        assert resp == "redirected"

        mock_service.add_template_data.assert_called_with(
            {"title": "NewT", "main_file": "f.svg", "last_world_file": "", "source": ""}
        )
        mock_flash.assert_called_with("Template 'NewT' added.", "success")


@patch("src.main_app.app_routes.admin_routes.templates.flash")
@patch("src.main_app.app_routes.admin_routes.templates.redirect")
@patch("src.main_app.app_routes.admin_routes.templates.url_for")
def test_add_template_missing_title(mock_url, mock_redirect, mock_flash, app_mock):
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with app_mock.test_request_context(method="POST", data={"title": ""}):
        resp = _add_template()
        assert resp == "redirected"
        mock_flash.assert_called_with("Title is required to add a template.", "danger")


@patch("src.main_app.app_routes.admin_routes.templates.template_service")
@patch("src.main_app.app_routes.admin_routes.templates.flash")
@patch("src.main_app.app_routes.admin_routes.templates.redirect")
@patch("src.main_app.app_routes.admin_routes.templates.url_for")
def test_update_template_success(mock_url, mock_redirect, mock_flash, mock_service, app_mock):
    mock_service.update_template_data.return_value = MagicMock(title="UpdT")
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with app_mock.test_request_context(method="POST", data={"id": 1, "title": "UpdT", "main_file": "f2.svg"}):
        resp = _update_template()
        assert resp == "redirected"

        mock_service.update_template_data.assert_called_with(
            1, {"title": "UpdT", "main_file": "f2.svg", "last_world_file": "", "source": ""}
        )
        mock_flash.assert_called_with("Template 'UpdT' main file: f2.svg updated.", "success")


@patch("src.main_app.app_routes.admin_routes.templates.flash")
@patch("src.main_app.app_routes.admin_routes.templates.redirect")
@patch("src.main_app.app_routes.admin_routes.templates.url_for")
def test_update_template_missing_id(mock_url, mock_redirect, mock_flash, app_mock):
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with app_mock.test_request_context(method="POST", data={"title": "UpdT"}):
        resp = _update_template()
        assert resp == "redirected"
        mock_flash.assert_called_with("Template ID is required to update a template.", "danger")


@patch("src.main_app.app_routes.admin_routes.templates.template_service")
@patch("src.main_app.app_routes.admin_routes.templates.flash")
@patch("src.main_app.app_routes.admin_routes.templates.redirect")
@patch("src.main_app.app_routes.admin_routes.templates.url_for")
def test_delete_template_success(mock_url, mock_redirect, mock_flash, mock_service, app_mock):
    mock_service.delete_template.return_value = MagicMock(title="DelT")
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with app_mock.test_request_context():
        resp = _delete_template(1)
        assert resp == "redirected"

        mock_service.delete_template.assert_called_with(1)
        mock_flash.assert_called_with("Template 'DelT' removed.", "success")


def test_Templates():
    # Verify routes registration
    bp = MagicMock()
    Templates(bp)

    # Should register 4 GET routes, 3 POST routes
    assert bp.get.call_count == 4
    assert bp.post.call_count == 3

    # Check endpoints
    bp.get.assert_any_call("/templates")
    bp.get.assert_any_call("/templates/<int:template_id>/edit")
    bp.get.assert_any_call("/templates-need-update")
    bp.get.assert_any_call("/templates/download-json")
    bp.post.assert_any_call("/templates/add")
    bp.post.assert_any_call("/templates/update")
    bp.post.assert_any_call("/templates/<int:template_id>/delete")


def test_create_json_file_success(app_mock, monkeypatch):
    """Test create_json_file returns JSON file with templates data."""
    from src.main_app.db import TemplateRecord
    from src.main_app.app_routes.admin_routes.templates import create_json_file

    templates = [
        TemplateRecord(
            id=1,
            title="Test Template",
            main_file="File:Example.svg",
            last_world_file="File:World.svg",
            last_world_year="2023",
            source="Test source",
            created_at=None,
            updated_at=None,
        ),
    ]
    monkeypatch.setattr(
        "src.main_app.app_routes.admin_routes.templates.template_service.list_templates", lambda: templates
    )

    response, status_code = create_json_file()

    assert status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert "attachment" in response.headers["Content-Disposition"]
    assert "templates.json" in response.headers["Content-Disposition"]


def test_create_json_file_no_templates(app_mock, monkeypatch):
    """Test create_json_file returns 404 when no templates."""
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.templates.template_service.list_templates", lambda: [])

    from src.main_app.app_routes.admin_routes.templates import create_json_file

    msg, status_code = create_json_file()

    assert status_code == 404
    assert "No templates found" in msg


def test_create_json_file_exception(app_mock, monkeypatch):
    """Test create_json_file returns 500 on exception."""

    def raise_error():
        raise RuntimeError("Database error")

    monkeypatch.setattr("src.main_app.app_routes.admin_routes.templates.template_service.list_templates", raise_error)

    from src.main_app.app_routes.admin_routes.templates import create_json_file

    msg, status_code = create_json_file()

    assert status_code == 500
    assert "Failed to create JSON file" in msg


def test_edit_template_found(app_mock, monkeypatch):
    """Test _edit_template returns template when found."""
    from src.main_app.db import TemplateRecord
    from src.main_app.app_routes.admin_routes.templates import _edit_template

    template = TemplateRecord(
        id=1,
        title="Test Template",
        main_file="File:Example.svg",
        last_world_file="",
        created_at=None,
        updated_at=None,
        source=None,
    )
    monkeypatch.setattr(
        "src.main_app.app_routes.admin_routes.templates.template_service.get_template", lambda id: template
    )

    with app_mock.test_request_context():
        with patch("src.main_app.app_routes.admin_routes.templates.render_template") as mock_render:
            mock_render.return_value = "rendered"
            result = _edit_template(1)
            assert result == "rendered"
            mock_render.assert_called_once()
            kwargs = mock_render.call_args[1]
            assert kwargs["template"] == template
            assert kwargs["error"] is None


def test_edit_template_not_found(app_mock, monkeypatch):
    """Test _edit_template returns error when template not found."""
    from src.main_app.app_routes.admin_routes.templates import _edit_template

    monkeypatch.setattr(
        "src.main_app.app_routes.admin_routes.templates.template_service.get_template",
        lambda id: (_ for _ in ()).throw(LookupError("Not found")),
    )

    with app_mock.test_request_context():
        with patch("src.main_app.app_routes.admin_routes.templates.render_template") as mock_render:
            mock_render.return_value = "rendered"
            result = _edit_template(999)
            assert result == "rendered"
            mock_render.assert_called_once()
            kwargs = mock_render.call_args[1]
            assert kwargs["template"] is None
            assert "not found" in kwargs["error"].lower()
