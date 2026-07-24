from unittest.mock import MagicMock, patch

from src.main_app.admin.routes.templates import (
    TemplatesRoutesFuncs,
)


@patch("src.main_app.admin.routes.templates.TemplateService.add_template_data")
@patch("src.main_app.admin.routes.templates.flash")
@patch("src.main_app.admin.routes.templates.redirect")
@patch("src.main_app.admin.routes.templates.url_for")
def test_add_template_success(mock_url, mock_redirect, mock_flash, mock_service, mock_app):
    mock_service.return_value = MagicMock(title="NewT")
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with mock_app.test_request_context(method="POST", data={"title": "NewT", "main_file": "f.svg"}):
        resp = TemplatesRoutesFuncs().add_template()
        assert resp == "redirected"

        mock_service.assert_called_with({"title": "NewT", "main_file": "f.svg", "last_world_file": "", "source": ""})
        mock_flash.assert_called_with("Template 'NewT' added.", "success")


@patch("src.main_app.admin.routes.templates.flash")
@patch("src.main_app.admin.routes.templates.redirect")
@patch("src.main_app.admin.routes.templates.url_for")
def test_add_template_missing_title(mock_url, mock_redirect, mock_flash, mock_app):
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with mock_app.test_request_context(method="POST", data={"title": ""}):
        resp = TemplatesRoutesFuncs().add_template()
        assert resp == "redirected"
        mock_flash.assert_called_with("Title is required to add a template.", "danger")


@patch("src.main_app.admin.routes.templates.TemplateService.update_template_data")
@patch("src.main_app.admin.routes.templates.flash")
@patch("src.main_app.admin.routes.templates.redirect")
@patch("src.main_app.admin.routes.templates.url_for")
def test_update_template_success(mock_url, mock_redirect, mock_flash, mock_service, mock_app):
    mock_service.return_value = MagicMock(title="UpdT")
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with mock_app.test_request_context(method="POST", data={"id": 1, "title": "UpdT", "main_file": "f2.svg"}):
        resp = TemplatesRoutesFuncs().update_template()
        assert resp == "redirected"

        mock_service.assert_called_with(
            1,
            {
                "title": "UpdT",
                "main_file": "f2.svg",
                "last_world_file": None,
                "source": None,
                "last_world_year": None,
            },
        )
        mock_flash.assert_called_with("Template 'UpdT' main file: f2.svg updated.", "success")


@patch("src.main_app.admin.routes.templates.flash")
@patch("src.main_app.admin.routes.templates.redirect")
@patch("src.main_app.admin.routes.templates.url_for")
def test_update_template_missing_id(mock_url, mock_redirect, mock_flash, mock_app):
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with mock_app.test_request_context(method="POST", data={"title": "UpdT"}):
        resp = TemplatesRoutesFuncs().update_template()
        assert resp == "redirected"
        mock_flash.assert_called_with("Template ID is required to update a template.", "danger")


@patch("src.main_app.admin.routes.templates.TemplateService.get_template")
@patch("src.main_app.admin.routes.templates.TemplateService.delete")
@patch("src.main_app.admin.routes.templates.flash")
@patch("src.main_app.admin.routes.templates.redirect")
@patch("src.main_app.admin.routes.templates.url_for")
def test_delete_template_success(
    mock_url, mock_redirect, mock_flash, mock_delete_template, mock_get_template, mock_app
):
    mock_get_template.return_value = MagicMock(title="DelT")
    mock_delete_template.return_value = True
    mock_url.return_value = "/dash"
    mock_redirect.return_value = "redirected"

    with mock_app.test_request_context():
        resp = TemplatesRoutesFuncs().delete_template(1)
        assert resp == "redirected"

        mock_get_template.assert_called_with(1)
        mock_delete_template.assert_called_with(1)
        mock_flash.assert_called_with("Template 'DelT' removed.", "success")


def test_create_json_file_success(mock_app, monkeypatch):
    """Test create_json_file returns JSON file with templates data."""
    from src.main_app.admin.routes.templates import create_json_file
    from src.main_app.db.models import TemplateRecord

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
        "src.main_app.admin.routes.templates.TemplateService.list_templates", lambda self, limit=None: templates
    )

    with mock_app.app_context():
        response, status_code = create_json_file()

    assert status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert "attachment" in response.headers["Content-Disposition"]
    assert "templates.json" in response.headers["Content-Disposition"]


def test_create_json_file_no_templates(mock_app, monkeypatch):
    """Test create_json_file returns 404 when no templates."""
    monkeypatch.setattr("src.main_app.admin.routes.templates.TemplateService.list_templates", list)

    from src.main_app.admin.routes.templates import create_json_file

    msg, status_code = create_json_file()

    assert status_code == 404
    assert "No templates found" in msg


def test_create_json_file_exception(mock_app, monkeypatch):
    """Test create_json_file returns 500 on exception."""

    def raise_error():
        raise RuntimeError("Database error")

    monkeypatch.setattr("src.main_app.admin.routes.templates.TemplateService.list_templates", raise_error)

    from src.main_app.admin.routes.templates import create_json_file

    msg, status_code = create_json_file()

    assert status_code == 500
    assert "Failed to create JSON file" in msg


def test_edit_template_found(mock_app, monkeypatch):
    """Test TemplatesRoutesFuncs().edit_template returns template when found."""
    from src.main_app.db.models import TemplateRecord

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
        "src.main_app.admin.routes.templates.TemplateService.get_template", lambda self, id: template
    )

    with mock_app.test_request_context():
        with patch("src.main_app.admin.routes.templates.render_template") as mock_render:
            mock_render.return_value = "rendered"
            result = TemplatesRoutesFuncs().edit_template(1)
            assert result == "rendered"
            mock_render.assert_called_once()
            kwargs = mock_render.call_args[1]
            assert kwargs["template"] == template
            assert kwargs["error"] is None


def test_edit_template_not_found(mock_app, monkeypatch):
    """Test TemplatesRoutesFuncs().edit_template returns error when template not found."""
    from src.main_app.admin.routes.templates import TemplatesRoutesFuncs

    monkeypatch.setattr(
        "src.main_app.admin.routes.templates.TemplateService.get_template",
        lambda self, id: (_ for _ in ()).throw(LookupError("Not found")),
    )

    with mock_app.test_request_context():
        with patch("src.main_app.admin.routes.templates.render_template") as mock_render:
            mock_render.return_value = "rendered"
            result = TemplatesRoutesFuncs().edit_template(999)
            assert result == "rendered"
            mock_render.assert_called_once()
            kwargs = mock_render.call_args[1]
            assert kwargs["template"] is None
            assert "not found" in kwargs["error"].lower()
