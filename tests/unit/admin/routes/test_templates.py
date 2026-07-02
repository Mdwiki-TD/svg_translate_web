"""
Unit tests for src/main_app/admin/routes/templates.py module.
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.main_app.admin.routes.templates import (
    _add_template,
    _delete_template,
    _edit_template,
    _edit_template_by_title,
    _update_template,
    create_json_file,
)


@pytest.mark.usefixtures("mock_app")
class TestTemplatesUnit:
    def test_create_json_file_success(self, monkeypatch):
        from src.main_app.db.models import TemplateRecord
        templates = [TemplateRecord(id=1, title="T1", main_file="f.svg", last_world_file="", last_world_year=None, source=None, created_at=None, updated_at=None)]
        monkeypatch.setattr("src.main_app.admin.routes.templates.list_templates", lambda: templates)
        response, status = create_json_file()
        assert status == 200
        assert "templates.json" in response.headers["Content-Disposition"]

    def test_create_json_file_no_templates(self, monkeypatch):
        monkeypatch.setattr("src.main_app.admin.routes.templates.list_templates", list)
        msg, status = create_json_file()
        assert status == 404
        assert "No templates found" in msg

    def test_create_json_file_lookup_error(self, monkeypatch):
        monkeypatch.setattr("src.main_app.admin.routes.templates.list_templates", Mock(side_effect=LookupError("not found")))
        msg, status = create_json_file()
        assert status == 404

    def test_create_json_file_exception(self, monkeypatch):
        monkeypatch.setattr("src.main_app.admin.routes.templates.list_templates", Mock(side_effect=RuntimeError("error")))
        msg, status = create_json_file()
        assert status == 500

    def test_add_template_missing_title(self, monkeypatch):
        mock_req = Mock()
        mock_req.form.get.return_value = ""
        monkeypatch.setattr("src.main_app.admin.routes.templates.request", mock_req)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.templates.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", lambda x: f"/{x}")
        result = _add_template()
        assert "redirect" in result
        mock_flash.assert_called()

    def test_add_template_success(self, monkeypatch):
        mock_req = Mock()
        def form_get(key, default=None, **kwargs):
            return {"title": "NewT", "main_file": "f.svg", "last_world_file": "", "source": ""}.get(key, default or "")
        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.templates.request", mock_req)
        mock_record = MagicMock()
        mock_record.title = "NewT"
        monkeypatch.setattr("src.main_app.admin.routes.templates.add_template_data", lambda d: mock_record)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.templates.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", lambda x: f"/{x}")
        _add_template()
        mock_flash.assert_called_with("Template 'NewT' added.", "success")

    def test_add_template_value_error(self, monkeypatch):
        mock_req = Mock()
        def form_get(key, default=None, **kwargs):
            return {"title": "Dup", "main_file": "", "last_world_file": "", "source": ""}.get(key, default or "")
        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.templates.request", mock_req)
        monkeypatch.setattr("src.main_app.admin.routes.templates.add_template_data", Mock(side_effect=ValueError("exists")))
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.templates.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", lambda x: f"/{x}")
        _add_template()
        mock_flash.assert_called()

    def test_update_template_missing_id(self, monkeypatch):
        mock_req = Mock()
        def form_get(key, default=None, **kwargs):
            return {"id": 0, "title": "T"}.get(key, default if default else "")
        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.templates.request", mock_req)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.templates.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", lambda x: f"/{x}")
        _update_template()
        mock_flash.assert_called_with("Template ID is required to update a template.", "danger")

    def test_update_template_success(self, monkeypatch):
        mock_req = Mock()
        def form_get(key, default=None, **kwargs):
            return {"id": 1, "title": "UpdT", "main_file": "f.svg", "from_popup": "0"}.get(key, default if default else "")
        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.templates.request", mock_req)
        mock_record = MagicMock()
        mock_record.title = "UpdT"
        monkeypatch.setattr("src.main_app.admin.routes.templates.update_template_data", lambda i, d: mock_record)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.templates.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", lambda x: f"/{x}")
        _update_template()
        mock_flash.assert_called()

    def test_update_template_lookup_error(self, monkeypatch):
        mock_req = Mock()
        def form_get(key, default=None, **kwargs):
            return {"id": 1, "title": "T", "main_file": "f.svg"}.get(key, default if default else "")
        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.templates.request", mock_req)
        monkeypatch.setattr("src.main_app.admin.routes.templates.update_template_data", Mock(side_effect=LookupError("not found")))
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.templates.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", lambda x: f"/{x}")
        _update_template()
        mock_flash.assert_called()

    def test_update_template_from_popup(self, monkeypatch):
        mock_req = Mock()
        def form_get(key, default=None, **kwargs):
            return {"id": 1, "title": "T", "main_file": "f.svg", "from_popup": "1"}.get(key, default if default else "")
        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.templates.request", mock_req)
        mock_record = MagicMock()
        mock_record.title = "T"
        monkeypatch.setattr("src.main_app.admin.routes.templates.update_template_data", lambda i, d: mock_record)
        monkeypatch.setattr("src.main_app.admin.routes.templates.flash", Mock())
        monkeypatch.setattr("src.main_app.admin.routes.templates.render_template", lambda t, **c: f"rendered:{t}")
        result = _update_template()
        assert "popup_action" in result

    def test_delete_template_success(self, monkeypatch):
        mock_record = MagicMock()
        mock_record.title = "DelT"
        monkeypatch.setattr("src.main_app.admin.routes.templates.get_template", lambda i: mock_record)
        monkeypatch.setattr("src.main_app.admin.routes.templates.delete_template", lambda i: None)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.templates.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", lambda x: f"/{x}")
        mock_req = Mock()
        def form_get(key, default=None, **kwargs):
            return {"from_popup": "0"}.get(key, default if default else "")
        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.templates.request", mock_req)
        _delete_template(1)
        mock_flash.assert_called_with("Template 'DelT' removed.", "success")

    def test_delete_template_not_found(self, monkeypatch):
        monkeypatch.setattr("src.main_app.admin.routes.templates.get_template", Mock(side_effect=LookupError("not found")))
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.templates.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.templates.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.templates.url_for", lambda x: f"/{x}")
        mock_req = Mock()
        def form_get(key, default=None, **kwargs):
            return {"from_popup": "0"}.get(key, default if default else "")
        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.templates.request", mock_req)
        _delete_template(999)
        mock_flash.assert_called()

    def test_delete_template_from_popup(self, monkeypatch):
        mock_record = MagicMock()
        mock_record.title = "DelT"
        monkeypatch.setattr("src.main_app.admin.routes.templates.get_template", lambda i: mock_record)
        monkeypatch.setattr("src.main_app.admin.routes.templates.delete_template", lambda i: None)
        mock_req = Mock()
        def form_get(key, default=None, **kwargs):
            return {"from_popup": "1"}.get(key, default if default else "")
        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.templates.request", mock_req)
        monkeypatch.setattr("src.main_app.admin.routes.templates.flash", Mock())
        monkeypatch.setattr("src.main_app.admin.routes.templates.render_template", lambda t, **c: f"rendered:{t}")
        result = _delete_template(1)
        assert "popup_action" in result

    def test_edit_template_found(self, monkeypatch):
        mock_template = MagicMock()
        monkeypatch.setattr("src.main_app.admin.routes.templates.get_template", lambda i: mock_template)
        monkeypatch.setattr("src.main_app.admin.routes.templates.render_template", lambda t, **c: c)
        result = _edit_template(1)
        assert result["template"] == mock_template
        assert result["error"] is None

    def test_edit_template_not_found(self, monkeypatch):
        monkeypatch.setattr("src.main_app.admin.routes.templates.get_template", Mock(side_effect=LookupError("not found")))
        monkeypatch.setattr("src.main_app.admin.routes.templates.render_template", lambda t, **c: c)
        result = _edit_template(999)
        assert result["template"] is None
        assert result["error"] == "Template not found"

    def test_edit_template_by_title_found(self, monkeypatch):
        mock_template = MagicMock()
        monkeypatch.setattr("src.main_app.admin.routes.templates.get_template_by_title", lambda t: mock_template)
        monkeypatch.setattr("src.main_app.admin.routes.templates.render_template", lambda t, **c: c)
        result = _edit_template_by_title("Test")
        assert result["template"] == mock_template
        assert result["error"] is None

    def test_edit_template_by_title_not_found(self, monkeypatch):
        monkeypatch.setattr("src.main_app.admin.routes.templates.get_template_by_title", Mock(side_effect=LookupError("not found")))
        monkeypatch.setattr("src.main_app.admin.routes.templates.render_template", lambda t, **c: c)
        result = _edit_template_by_title("Missing")
        assert result["template"] is None
        assert result["error"] == "Template not found"
