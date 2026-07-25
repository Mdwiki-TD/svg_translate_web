"""
Unit tests for src/main_app/adminpanel/routes/owid_charts.py module.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, Mock

import pytest

from src.main_app.admin.routes.owid_charts import OwidCharts
from src.main_app.db.services import ViewsService


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.owid_charts_service = OwidCharts()

    @pytest.fixture(autouse=True)
    def setup_mocks(self, monkeypatch):
        self.mock_flash = Mock()
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.flash", self.mock_flash)

        self.mock_redirect = Mock(side_effect=lambda x, **kw: f"redirect:{x}")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.redirect", self.mock_redirect)

        self.mock_url_for = Mock(side_effect=lambda x, **kw: f"/{x}")
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.url_for", self.mock_url_for)

        self.mock_render_template = Mock(side_effect=lambda t, **c: c)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.render_template", self.mock_render_template)

        self.mock_delete_chart = MagicMock(return_value=True)
        monkeypatch.setattr("src.main_app.admin.routes.owid_charts.OwidChartsService.delete", self.mock_delete_chart)

        self.mock_list_templates = MagicMock(return_value=[])
        monkeypatch.setattr(ViewsService, "list_owid_charts_templates", self.mock_list_templates)


class TestSetupWithMockService(TestSetup):
    """For test classes that stub out the owid_charts_service instance entirely.

    TestDeleteChart intentionally does NOT use this — it exercises the real service
    instance and only patches OwidChartsService.delete at the class level, so forcing
    a generic instance mock on it would silently swallow that patch.
    """

    @pytest.fixture(autouse=True)
    def setup_mock_service(self):
        self.mock_owid_charts_service = MagicMock()
        self.owid_charts_service.owid_charts_service = self.mock_owid_charts_service


class TestCreateJsonFile(TestSetupWithMockService):
    def test_success(self):
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
        self.mock_owid_charts_service.list_charts.return_value = [mock_chart]

        response, status = self.owid_charts_service.create_json_file()
        assert status == 200
        assert "owid_charts.json" in response.headers["Content-Disposition"]

    def test_no_charts(self):
        self.mock_owid_charts_service.list_charts.return_value = []

        msg, status = self.owid_charts_service.create_json_file()
        assert status == 404
        assert "No charts found" in msg

    def test_lookup_error(self):
        self.mock_owid_charts_service.list_charts.side_effect = LookupError("not found")

        msg, status = self.owid_charts_service.create_json_file()
        assert status == 404
        assert "Charts not found" in msg

    def test_exception(self):
        self.mock_owid_charts_service.list_charts.side_effect = RuntimeError("error")

        msg, status = self.owid_charts_service.create_json_file()
        assert status == 500
        assert "Failed to create JSON file" in msg

    def test_includes_template_info(self):
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
        self.mock_owid_charts_service.list_charts.return_value = [mock_chart]
        self.mock_list_templates.return_value = [mock_template]

        response, status = self.owid_charts_service.create_json_file()
        data = json.loads(response.get_data())
        assert data[0]["template_id"] == 42
        assert data[0]["template_title"] == "Template:T"


class TestAddChart(TestSetupWithMockService):
    def test_missing_slug(self):
        self.owid_charts_service._add_chart({"slug": "", "title": "T", "from_popup": "0"})

    def test_success(self):
        mock_record = MagicMock()
        mock_record.title = "T"
        self.mock_owid_charts_service.add_chart.return_value = mock_record

        self.owid_charts_service._add_chart({"slug": "s", "title": "T", "from_popup": "0"})

    def test_value_error(self):
        self.mock_owid_charts_service.add_chart.side_effect = ValueError("error")

        self.owid_charts_service._add_chart({"slug": "s", "title": "T", "from_popup": "0"})

    def test_from_popup_error(self):
        self.mock_owid_charts_service.add_chart.side_effect = ValueError("error")
        self.mock_redirect.side_effect = lambda *a, **kw: "redirected"
        self.mock_url_for.side_effect = lambda x, **kw: "/r"

        result = self.owid_charts_service._add_chart({"slug": "s", "title": "T", "from_popup": "1"})
        assert "redirected" in result


class TestUpdateChart(TestSetupWithMockService):
    def test_missing_slug(self):
        self.owid_charts_service._update_chart({"chart_id": "1", "slug": "", "title": "T"})

    def test_lookup_error(self):
        self.mock_owid_charts_service.update_chart_data.side_effect = LookupError("not found")

        self.owid_charts_service._update_chart({"chart_id": "1", "slug": "s", "title": "T", "from_popup": "0"})

    def test_success(self):
        mock_record = MagicMock()
        mock_record.title = "T"
        self.mock_owid_charts_service.update_chart_data.return_value = mock_record

        self.owid_charts_service._update_chart({"chart_id": "1", "slug": "s", "title": "T", "from_popup": "0"})

    def test_record_none(self):
        self.mock_owid_charts_service.update_chart_data.return_value = None

        self.owid_charts_service._update_chart({"chart_id": "1", "slug": "s", "title": "T", "from_popup": "0"})

    def test_from_popup_error(self):
        self.mock_owid_charts_service.update_chart_data.side_effect = LookupError("not found")
        self.mock_redirect.side_effect = lambda *a, **kw: "redirected"
        self.mock_url_for.side_effect = lambda x, **kw: "/r"

        result = self.owid_charts_service._update_chart({"chart_id": "1", "slug": "s", "title": "T", "from_popup": "1"})
        assert "redirected" in result


class TestDeleteChart(TestSetup):
    def test_success(self):
        self.mock_delete_chart.return_value = True

        self.owid_charts_service._delete_chart(1, False)
        self.mock_flash.assert_called_with("Chart '1' removed.", "success")

    def test_not_found(self):
        self.mock_delete_chart.return_value = False

        self.owid_charts_service._delete_chart(999, False)
        self.mock_flash.assert_called_with("Chart '999' not found.", "warning")

    def test_from_popup(self):
        self.mock_delete_chart.return_value = True
        self.mock_render_template.side_effect = lambda t, **c: f"rendered:{t}"

        result = self.owid_charts_service._delete_chart(1, True)
        assert "popup_action" in result


class TestEditChart(TestSetupWithMockService):
    def test_found(self):
        mock_chart = MagicMock()
        self.mock_owid_charts_service.get_chart_by_id.return_value = mock_chart

        result = self.owid_charts_service._edit_chart(1)
        assert result["chart"] == mock_chart  # pyright: ignore[reportCallIssue]
        assert result["error"] is None  # pyright: ignore[reportCallIssue]
