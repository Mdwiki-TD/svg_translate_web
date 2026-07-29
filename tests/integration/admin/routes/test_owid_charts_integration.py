"""Tests for src.main_app.admin.routes.owid_charts.py"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from src.main_app import create_app
from src.main_app.config import TestingConfig
from src.main_app.db.models import OwidChartRecord
from src.main_app.db.services import OwidChartsService
from src.main_app.extensions import db as _db


@pytest.fixture
def sample_chart_record():
    """Create a sample OwidChartRecord."""
    return OwidChartRecord(
        chart_id=1,
        slug="test-chart",
        title="Test Chart",
        has_map_tab=True,
        max_time=2024,
        min_time=2000,
        default_tab="chart",
        is_published=True,
        single_year_data=False,
        len_years=25,
        has_timeline=True,
    )


@pytest.fixture
def owid_charts_admin_client(monkeypatch: pytest.MonkeyPatch):
    """Return a configured Flask test client with real OWID charts service."""
    admin_user = SimpleNamespace(username="admin_user", is_active_admin=True)

    def fake_current_user():
        return admin_user

    monkeypatch.setenv("FLASK_SECRET_KEY", "testing-secret")
    monkeypatch.setattr("src.main_app.public.auth.utils.load_user", fake_current_user)
    monkeypatch.setattr("src.main_app.admin.decorators.load_user", fake_current_user)

    flask_app = create_app(TestingConfig)
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    with flask_app.app_context():
        real_tables = [t for t in _db.metadata.tables.values() if not t.info.get("is_view")]
        _db.metadata.create_all(_db.engine, tables=real_tables)
        yield flask_app.test_client()
        _db.session.remove()
        _db.metadata.drop_all(_db.engine, tables=real_tables)


class TestOwidChartsDashboard:
    """Tests for the OWID charts dashboard route."""

    def test_dashboard_renders_with_no_charts(self, owid_charts_admin_client):
        """Test dashboard renders when no charts exist."""
        response = owid_charts_admin_client.get("/adminpanel/owidcharts")
        assert response.status_code == 200

    def test_dashboard_renders_with_charts(self, owid_charts_admin_client, sample_chart_record):
        """Test dashboard renders with charts."""
        svc = OwidChartsService()
        svc.add_chart(
            slug=sample_chart_record.slug,
            title=sample_chart_record.title,
            has_map_tab=sample_chart_record.has_map_tab,
            max_time=sample_chart_record.max_time,
            min_time=sample_chart_record.min_time,
            default_tab=sample_chart_record.default_tab,
            is_published=sample_chart_record.is_published,
            single_year_data=sample_chart_record.single_year_data,
            len_years=sample_chart_record.len_years,
            has_timeline=sample_chart_record.has_timeline,
        )

        response = owid_charts_admin_client.get("/adminpanel/owidcharts")
        assert response.status_code == 200

    def test_dashboard_filter_has_template(self, owid_charts_admin_client):
        """Test dashboard filters charts with templates."""
        svc = OwidChartsService()
        svc.add_chart(slug="chart1", title="Chart 1")
        svc.add_chart(slug="chart2", title="Chart 2")

        response = owid_charts_admin_client.get("/adminpanel/owidcharts?template=has_template")
        assert response.status_code == 200

    def test_dashboard_filter_no_template(self, owid_charts_admin_client):
        """Test dashboard filters charts without templates."""
        svc = OwidChartsService()
        svc.add_chart(slug="chart2", title="Chart 2")

        response = owid_charts_admin_client.get("/adminpanel/owidcharts?template=no_template")
        assert response.status_code == 200


class TestAddChartPopup:
    """Tests for the add chart popup route."""

    def test_add_chart_popup_renders(self, owid_charts_admin_client):
        """Test add chart popup renders."""
        response = owid_charts_admin_client.get("/adminpanel/owidcharts/add")
        assert response.status_code == 200


class TestAddChart:
    """Tests for the add chart POST route."""

    def test_add_chart_success(self, owid_charts_admin_client):
        """Test adding a chart successfully."""
        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/add",
            data={
                "slug": "new-chart",
                "title": "New Chart",
                "has_map_tab": "on",
                "is_published": "on",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        svc = OwidChartsService()
        assert svc.get_chart_by_slug("new-chart") is not None

    def test_add_chart_missing_slug(self, owid_charts_admin_client):
        """Test adding a chart without slug redirects with flash."""
        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/add",
            data={
                "slug": "",
                "title": "New Chart",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_add_chart_missing_title(self, owid_charts_admin_client):
        """Test adding a chart without title redirects with flash."""
        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/add",
            data={
                "slug": "new-chart",
                "title": "",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_add_chart_with_all_options(self, owid_charts_admin_client):
        """Test adding a chart with all options set."""
        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/add",
            data={
                "slug": "full-chart",
                "title": "Full Chart",
                "has_map_tab": "on",
                "max_time": "2024",
                "min_time": "2000",
                "default_tab": "table",
                "is_published": "on",
                "single_year_data": "1",
                "len_years": "25",
                "has_timeline": "1",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        svc = OwidChartsService()
        chart = svc.get_chart_by_slug("full-chart")
        assert chart is not None
        assert chart.has_map_tab is True
        assert chart.max_time == 2024
        assert chart.min_time == 2000
        assert chart.default_tab == "table"
        assert chart.is_published is True
        assert chart.single_year_data is True
        assert chart.len_years == 25
        assert chart.has_timeline is True


class TestUpdateChart:
    """Tests for the update chart POST route."""

    def test_update_chart_success(self, owid_charts_admin_client):
        """Test updating a chart successfully."""
        svc = OwidChartsService()
        created = svc.add_chart(slug="update-me", title="Update Me")

        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/update",
            data={
                "chart_id": str(created.chart_id),
                "slug": "updated-chart",
                "title": "Updated Chart",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        updated = svc.get_chart_by_id(created.chart_id)
        assert updated.slug == "updated-chart"
        assert updated.title == "Updated Chart"

    def test_update_chart_missing_id(self, owid_charts_admin_client):
        """Test updating without chart_id redirects."""
        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/update",
            data={
                "slug": "updated",
                "title": "updated",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_update_chart_missing_slug(self, owid_charts_admin_client):
        """Test updating without slug redirects with flash."""
        svc = OwidChartsService()
        created = svc.add_chart(slug="chart-x", title="Chart X")

        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/update",
            data={
                "chart_id": str(created.chart_id),
                "slug": "",
                "title": "updated",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200

    def test_update_chart_from_popup(self, owid_charts_admin_client):
        """Test updating a chart from popup renders popup action."""
        svc = OwidChartsService()
        created = svc.add_chart(slug="popup-chart", title="Popup Chart")

        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/update",
            data={
                "chart_id": str(created.chart_id),
                "slug": "updated",
                "title": "updated",
                "from_popup": "1",
            },
        )
        assert response.status_code == 200


class TestDeleteChart:
    """Tests for the delete chart POST route."""

    def test_delete_chart_success(self, owid_charts_admin_client):
        """Test deleting a chart successfully."""
        svc = OwidChartsService()
        created = svc.add_chart(slug="delete-me", title="Delete Me")

        response = owid_charts_admin_client.post(
            f"/adminpanel/owidcharts/{created.chart_id}/delete",
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert svc.get_chart_by_id(created.chart_id) is None

    def test_delete_chart_not_found(self, owid_charts_admin_client):
        """Test deleting a non-existent chart shows error."""
        response = owid_charts_admin_client.post("/adminpanel/owidcharts/999/delete", follow_redirects=True)
        assert response.status_code == 200

    def test_delete_chart_from_popup(self, owid_charts_admin_client):
        """Test deleting a chart from popup renders popup action."""
        svc = OwidChartsService()
        created = svc.add_chart(slug="popup-del", title="Popup Del")

        response = owid_charts_admin_client.post(
            f"/adminpanel/owidcharts/{created.chart_id}/delete",
            data={"from_popup": "1"},
        )
        assert response.status_code == 200


class TestEditChart:
    """Tests for the edit chart GET route."""

    def test_edit_chart_success(self, owid_charts_admin_client):
        """Test editing a chart renders edit page."""
        svc = OwidChartsService()
        created = svc.add_chart(slug="edit-me", title="Edit Me")

        response = owid_charts_admin_client.get(f"/adminpanel/owidcharts/{created.chart_id}/edit")
        assert response.status_code == 200


class TestDownloadJson:
    """Tests for the download JSON route."""

    def test_download_json_success(self, owid_charts_admin_client):
        """Test downloading charts as JSON."""
        svc = OwidChartsService()
        svc.add_chart(slug="test-chart", title="Test Chart")

        response = owid_charts_admin_client.get("/adminpanel/owidcharts/download-json")

        assert response.status_code == 200
        assert response.content_type == "application/json"
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]["slug"] == "test-chart"

    def test_download_json_no_charts(self, owid_charts_admin_client):
        """Test downloading JSON when no charts exist redirects."""
        response = owid_charts_admin_client.get("/adminpanel/owidcharts/download-json", follow_redirects=True)
        assert response.status_code == 200

    def test_download_json_multiple_charts(self, owid_charts_admin_client):
        """Test downloading multiple charts as JSON."""
        svc = OwidChartsService()
        for i in range(1, 4):
            svc.add_chart(slug=f"chart-{i}", title=f"Chart {i}")

        response = owid_charts_admin_client.get("/adminpanel/owidcharts/download-json")

        data = json.loads(response.data)
        assert len(data) == 3
        assert data[0]["slug"] == "chart-1"
        assert data[2]["slug"] == "chart-3"

    def test_download_json_includes_all_fields(self, owid_charts_admin_client):
        """Test that JSON export includes all chart fields."""
        svc = OwidChartsService()
        svc.add_chart(slug="test-chart", title="Test Chart")

        response = owid_charts_admin_client.get("/adminpanel/owidcharts/download-json")

        data = json.loads(response.data)[0]
        expected_fields = [
            "chart_id",
            "slug",
            "title",
            "has_map_tab",
            "max_time",
            "min_time",
            "default_tab",
            "is_published",
            "single_year_data",
            "len_years",
            "has_timeline",
        ]
        for field in expected_fields:
            assert field in data
