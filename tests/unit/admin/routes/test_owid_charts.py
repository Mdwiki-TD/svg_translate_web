"""
Unit tests for src/main_app/admin/routes/owid_charts.py module.
"""

from __future__ import annotations

from unittest.mock import MagicMock, Mock

from src.main_app.admin.routes.owid_charts import (
    _add_chart,
    _add_chart_popup,
    _delete_chart,
    _edit_chart,
    _update_chart,
    create_json_file,
)


class TestCreateJsonFile:
    def test_success(self, monkeypatch):
        mock_chart = MagicMock()
        mock_chart.chart_id = 1
        mock_chart.slug = "test"
        mock_chart.title = "Test"
        mock_chart.has_map_tab = False
        mock_chart.max_time = None
        mock_chart.min_time = None
        mock_chart.default_tab = None
        mock_chart.is_published = False
        mock_chart.single_year_data = False
        mock_chart.len_years = None
        mock_chart.has_timeline = False
        mock_svc = MagicMock()
        mock_svc.list_charts.return_value = [mock_chart]
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.list_owid_charts_templates", list)
        response, status = create_json_file()
        assert status == 200
        assert "owid_charts.json" in response.headers["Content-Disposition"]

    def test_no_charts(self, monkeypatch):
        mock_svc = MagicMock()
        mock_svc.list_charts.return_value = []
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.list_owid_charts_templates", list)
        msg, status = create_json_file()
        assert status == 404
        assert "No charts found" in msg

    def test_lookup_error(self, monkeypatch):
        mock_svc = MagicMock()
        mock_svc.list_charts.side_effect = LookupError("not found")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.list_owid_charts_templates", list)
        msg, status = create_json_file()
        assert status == 404
        assert "Charts not found" in msg

    def test_exception(self, monkeypatch):
        mock_svc = MagicMock()
        mock_svc.list_charts.side_effect = RuntimeError("error")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.list_owid_charts_templates", list)
        msg, status = create_json_file()
        assert status == 500
        assert "Failed to create JSON file" in msg

    def test_includes_template_info(self, monkeypatch):
        mock_chart = MagicMock()
        mock_chart.chart_id = 1
        mock_chart.slug = "t"
        mock_chart.title = "T"
        mock_chart.has_map_tab = False
        mock_chart.max_time = None
        mock_chart.min_time = None
        mock_chart.default_tab = None
        mock_chart.is_published = False
        mock_chart.single_year_data = False
        mock_chart.len_years = None
        mock_chart.has_timeline = False
        mock_template = MagicMock()
        mock_template.chart_id = 1
        mock_template.template_id = 42
        mock_template.template_title = "Template:T"
        mock_svc = MagicMock()
        mock_svc.list_charts.return_value = [mock_chart]
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.list_owid_charts_templates", lambda: [mock_template])
        response, status = create_json_file()
        import json as j

        data = j.loads(response.get_data())
        assert data[0]["template_id"] == 42
        assert data[0]["template_title"] == "Template:T"


class TestAddChartPopup:
    def test_renders(self, monkeypatch):
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.render_template", lambda t: f"rendered:{t}")
        result = _add_chart_popup()
        assert "add" in result


class TestAddChart:
    def test_missing_slug(self, monkeypatch):
        mock_req = Mock()

        def form_get(key, default=None, **kwargs):
            return {"slug": "", "title": "T", "from_popup": "0"}.get(key, default if default else "")

        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.request", mock_req)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.url_for", lambda x: f"/{x}")
        _add_chart()
        mock_flash.assert_called_with("Slug and Title are required.", "danger")

    def test_success(self, monkeypatch):
        mock_req = Mock()

        def form_get(key, default=None, **kwargs):
            return {"slug": "s", "title": "T", "from_popup": "0"}.get(key, default if default else "")

        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.request", mock_req)
        mock_record = MagicMock()
        mock_record.title = "T"
        mock_svc = MagicMock()
        mock_svc.add_chart.return_value = mock_record
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.url_for", lambda x: f"/{x}")
        _add_chart()
        mock_flash.assert_called()

    def test_value_error(self, monkeypatch):
        mock_req = Mock()

        def form_get(key, default=None, **kwargs):
            return {"slug": "s", "title": "T", "from_popup": "0"}.get(key, default if default else "")

        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.request", mock_req)
        mock_svc = MagicMock()
        mock_svc.add_chart.side_effect = ValueError("error")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.url_for", lambda x: f"/{x}")
        _add_chart()
        mock_flash.assert_called()

    def test_from_popup_error(self, monkeypatch):
        mock_req = Mock()

        def form_get(key, default=None, **kwargs):
            return {"slug": "s", "title": "T", "from_popup": "1"}.get(key, default if default else "")

        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.request", mock_req)
        mock_svc = MagicMock()
        mock_svc.add_chart.side_effect = ValueError("error")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.redirect", Mock(return_value="redirected"))
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.url_for", lambda x, **kw: "/r")
        result = _add_chart()
        assert "redirected" in result


class TestUpdateChart:
    def test_missing_slug(self, monkeypatch):
        mock_req = Mock()

        def form_get(key, default=None, **kwargs):
            return {"chart_id": "1", "slug": "", "title": "T"}.get(key, default if default else "")

        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.request", mock_req)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.url_for", lambda x, **kw: f"/{x}")
        _update_chart()
        mock_flash.assert_called()

    def test_lookup_error(self, monkeypatch):
        mock_req = Mock()

        def form_get(key, default=None, **kwargs):
            return {"chart_id": "1", "slug": "s", "title": "T", "from_popup": "0"}.get(key, default if default else "")

        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.request", mock_req)
        mock_svc = MagicMock()
        mock_svc.update_chart_data.side_effect = LookupError("not found")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.url_for", lambda x, **kw: f"/{x}")
        _update_chart()
        mock_flash.assert_called()

    def test_success(self, monkeypatch):
        mock_req = Mock()

        def form_get(key, default=None, **kwargs):
            return {"chart_id": "1", "slug": "s", "title": "T", "from_popup": "0"}.get(key, default if default else "")

        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.request", mock_req)
        mock_record = MagicMock()
        mock_record.title = "T"
        mock_svc = MagicMock()
        mock_svc.update_chart_data.return_value = mock_record
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.url_for", lambda x, **kw: f"/{x}")
        _update_chart()
        mock_flash.assert_called()

    def test_record_none(self, monkeypatch):
        mock_req = Mock()

        def form_get(key, default=None, **kwargs):
            return {"chart_id": "1", "slug": "s", "title": "T", "from_popup": "0"}.get(key, default if default else "")

        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.request", mock_req)
        mock_svc = MagicMock()
        mock_svc.update_chart_data.return_value = None
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.url_for", lambda x, **kw: f"/{x}")
        _update_chart()
        mock_flash.assert_called()

    def test_from_popup_error(self, monkeypatch):
        mock_req = Mock()

        def form_get(key, default=None, **kwargs):
            return {"chart_id": "1", "slug": "s", "title": "T", "from_popup": "1"}.get(key, default if default else "")

        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.request", mock_req)
        mock_svc = MagicMock()
        mock_svc.update_chart_data.side_effect = LookupError("not found")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.flash", Mock())
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.redirect", Mock(return_value="redirected"))
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.url_for", lambda x, **kw: "/r")
        result = _update_chart()
        assert "redirected" in result


class TestDeleteChart:
    def test_success(self, monkeypatch):
        mock_req = Mock()

        def form_get(key, default=None, **kwargs):
            return {"from_popup": "0"}.get(key, default if default else "")

        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.request", mock_req)
        mock_svc = MagicMock()
        mock_svc.delete_chart.return_value = True
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.delete_chart", mock_svc.delete_chart)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.url_for", lambda x: f"/{x}")
        _delete_chart(1)
        mock_flash.assert_called_with("Chart '1' removed.", "success")

    def test_not_found(self, monkeypatch):
        mock_req = Mock()

        def form_get(key, default=None, **kwargs):
            return {"from_popup": "0"}.get(key, default if default else "")

        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.request", mock_req)
        mock_svc = MagicMock()
        mock_svc.delete_chart.return_value = False
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.delete_chart", mock_svc.delete_chart)
        mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.flash", mock_flash)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.redirect", lambda x: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.url_for", lambda x: f"/{x}")
        _delete_chart(999)
        mock_flash.assert_called_with("Chart '999' not found.", "warning")

    def test_from_popup(self, monkeypatch):
        mock_req = Mock()

        def form_get(key, default=None, **kwargs):
            return {"from_popup": "1"}.get(key, default if default else "")

        mock_req.form.get = form_get
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.request", mock_req)
        mock_svc = MagicMock()
        mock_svc.delete_chart.return_value = True
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.delete_chart", mock_svc.delete_chart)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.flash", Mock())
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.render_template", lambda t, **c: f"rendered:{t}")
        result = _delete_chart(1)
        assert "popup_action" in result


class TestEditChart:
    def test_found(self, monkeypatch):
        mock_chart = MagicMock()
        mock_svc = MagicMock()
        mock_svc.get_chart_by_id.return_value = mock_chart
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.render_template", lambda t, **c: c)
        result = _edit_chart(1)
        assert result["chart"] == mock_chart
        assert result["error"] is None

    def test_not_found(self, monkeypatch):
        mock_svc = MagicMock()
        mock_svc.get_chart_by_id.side_effect = LookupError("not found")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.owid_charts_service", mock_svc)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.render_template", lambda t, **c: c)
        result = _edit_chart(999)
        assert result["chart"] is None
        assert result["error"] == "Chart not found"
