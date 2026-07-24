"""
Unit tests for src/main_app/adminpanel/routes/templates.py module.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.admin.routes.templates import TemplatesRoutesFuncs
from src.main_app.db.exceptions import DuplicateRecordError


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    """Mock template admin route dependencies."""

    mocks = MagicMock()
    mocks.update_template_data = MagicMock()
    mocks.add_template_data = MagicMock()
    mocks.list_templates = MagicMock()
    mocks.get_template = MagicMock()
    mocks.get_template_by_title = MagicMock()
    mocks.delete = MagicMock()
    mocks.flash = MagicMock()
    monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", lambda x: f"/{x}")

    monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", lambda x: f"redirect:{x}")
    monkeypatch.setattr( "src.main_app.admin.routes.templates.TemplateService.list_templates", mocks.list_templates )
    monkeypatch.setattr( "src.main_app.admin.routes.templates.TemplateService.add_template_data", mocks.add_template_data )
    monkeypatch.setattr( "src.main_app.admin.routes.templates.TemplateService.update_template_data", mocks.update_template_data )
    monkeypatch.setattr( "src.main_app.admin.routes.templates.TemplateService.get_template", mocks.get_template )
    monkeypatch.setattr( "src.main_app.admin.routes.templates.TemplateService.get_template_by_title", mocks.get_template_by_title )
    monkeypatch.setattr( "src.main_app.admin.routes.templates.TemplateService.delete", mocks.delete )
    monkeypatch.setattr("src.main_app.admin.routes.templates.flash", mocks.flash)
    monkeypatch.setattr("src.main_app.admin.routes.templates.render_template", lambda t, **c: c)
    return mocks


@pytest.mark.usefixtures("mock_app")
class TestTemplatesUnit:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.service = TemplatesRoutesFuncs()

    def test_create_json_file_success(self, mock_services):

        templates = [
            TemplateRecord(
                id=1,
                title="T1",
                main_file="f.svg",
                last_world_file="",
                last_world_year=None,
                source=None,
                created_at=None,
                updated_at=None,
            )
        ]
        mock_services.list_templates.return_value=templates

        response, status = self.service.create_json_file()
        assert status == 200
        assert "templates.json" in response.headers["Content-Disposition"]

    def test_create_json_file_no_templates(self, mock_services):
        mock_services.list_templates.return_value=[]

        msg, status = self.service.create_json_file()
        assert status == 404
        assert "No templates found" in msg

    def test_create_json_file_lookup_error(self, mock_services):
        mock_services.list_templates.return_value=None
        msg, status = self.service.create_json_file()
        assert status == 404

    def test_add_template_missing_title(self, mock_services):

        result = self.service._add_template({})
        assert "redirect" in result
        mock_services.flash.assert_called()

    def test_add_template_success(self, mock_services):
        mock_record = MagicMock()
        mock_record.title = "NewT"
        mock_services.add_template_data.return_value=mock_record

        self.service._add_template({"title": "NewT", "main_file": "f.svg", "last_world_file": "", "source": ""})
        mock_services.flash.assert_called_with("Template 'NewT' added.", "success")

    def test_add_template_value_error(self, mock_services):
        mock_services.add_template_data.side_effect=DuplicateRecordError("exists")

        self.service._add_template({"title": "Dup", "main_file": "", "last_world_file": "", "source": ""})
        mock_services.flash.assert_called()

    def test_update_template_missing_id(self, mock_services):

        self.service._update_template({})
        mock_services.flash.assert_called_with("Template ID is required to update a template.", "danger")

    def test_update_template_success(self, mock_services):
        mock_record = MagicMock()
        mock_record.title = "UpdT"
        mock_services.update_template_data.return_value = mock_record

        self.service._update_template({"id": 1, "title": "UpdT", "main_file": "f.svg", "from_popup": "0"})
        mock_services.flash.assert_called()

    def test_update_template_lookup_error(self, mock_services):

        mock_services.update_template_data.side_effect=LookupError("not found")

        self.service._update_template({"id": 1, "title": "T", "main_file": "f.svg"})
        mock_services.update_template_data.assert_called()

    def test_update_template_from_popup(self, mock_services):
        mock_record = MagicMock()
        mock_record.title = "T"
        mock_services.update_template_data.return_value = mock_record


        result = self.service._update_template({"id": 1, "title": "T", "main_file": "f.svg", "from_popup": "1"})
        assert result == {}
        # assert "popup_action" in result

    def test_delete_template_success(self, mock_services):
        mock_record = MagicMock()
        mock_record.title = "DelT"
        mock_services.get_template.return_value = mock_record


        self.service._delete_template(1, False)
        mock_services.flash.assert_called_with("Template 'DelT' removed.", "success")

    def test_delete_template_not_found(self, mock_services):
        mock_services.get_template.return_value = None

        self.service._delete_template(999, False)
        mock_services.flash.assert_called()

    def test_delete_template_from_popup(self, mock_services):
        mock_record = MagicMock()
        mock_record.title = "DelT"
        mock_services.get_template.return_value = mock_record

        result = self.service._delete_template(1, True)
        assert result == {}
        # assert "popup_action" in result

    def test_edit_template_found(self, mock_services):
        mock_template = MagicMock()
        mock_services.get_template.return_value = mock_template

        result = self.service.edit_template(1)
        assert result["template"] == mock_template  # pyright: ignore[reportCallIssue]
        assert result["error"] is None  # pyright: ignore[reportCallIssue]

    def test_edit_template_not_found(self, mock_services):
        mock_services.get_template.return_value = None


        result = self.service.edit_template(999)
        assert result["template"] is None  # pyright: ignore[reportCallIssue]
        assert result["error"] == "Template not found"  # pyright: ignore[reportCallIssue]

    def test_edit_template_by_title_found(self, mock_services):
        mock_template = MagicMock()
        mock_services.get_template_by_title.return_value = mock_template

        result = self.service.edit_by_title("Test")
        assert result["template"] == mock_template  # pyright: ignore[reportCallIssue]
        assert result["error"] is None  # pyright: ignore[reportCallIssue]

    def test_edit_template_by_title_not_found(self, mock_services):
        mock_services.get_template_by_title.return_value = None

        result = self.service.edit_by_title("Missing")
        assert result["template"] is None  # pyright: ignore[reportCallIssue]
        assert result["error"] == "Template not found"  # pyright: ignore[reportCallIssue]
