"""Tests for src.main_app.app_routes.admin_routes.owid_charts.py"""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, List
from unittest.mock import MagicMock, patch

import pytest

from src.main_app import create_app
from src.main_app.db.db_OwidCharts import OwidChartRecord


@dataclass
class FakeUser:
    """Fake user for testing."""

    user_id: str = "1"
    username: str = "admin_user"


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
def owid_charts_admin_client(monkeypatch: pytest.MonkeyPatch, sample_chart_record):
    """Return a configured Flask test client with mocked OWID charts service."""
    admin_user = SimpleNamespace(username="admin_user")

    def fake_current_user():
        return admin_user

    monkeypatch.setenv("FLASK_SECRET_KEY", "testing-secret")
    monkeypatch.setattr("src.main_app.services.users_service.current_user", fake_current_user)
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.owid_charts.current_user", fake_current_user)
    monkeypatch.setattr("src.main_app.app_routes.admin.admins_required.current_user", fake_current_user)
    monkeypatch.setattr("src.main_app.app_routes.admin.admins_required.active_coordinators", lambda: {admin_user.username})
    monkeypatch.setattr("src.main_app.services.admin_service.active_coordinators", lambda: {admin_user.username})
    monkeypatch.setattr("src.main_app.services.users_service.active_coordinators", lambda: {admin_user.username})

    mock_service = MagicMock()
    mock_service.list_charts.return_value = []
    monkeypatch.setattr("src.main_app.app_routes.admin_routes.owid_charts.owid_charts_service", mock_service)

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    yield flask_app.test_client(), mock_service


class TestOwidChartsDashboard:
    """Tests for the OWID charts dashboard route."""

    def test_dashboard_renders_with_no_charts(self, owid_charts_admin_client):
        """Test dashboard renders when no charts exist."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.list_charts.return_value = []

        response = flask_client.get("/admin/owid-charts")

        assert response.status_code == 200

    def test_dashboard_renders_with_charts(self, owid_charts_admin_client, sample_chart_record):
        """Test dashboard renders with charts."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.list_charts.return_value = [sample_chart_record]

        response = flask_client.get("/admin/owid-charts")

        assert response.status_code == 200

    def test_dashboard_filter_has_template(self, owid_charts_admin_client):
        """Test dashboard filters charts with templates."""
        flask_client, mock_service = owid_charts_admin_client
        chart_with_template = OwidChartRecord(
            chart_id=1,
            slug="chart1",
            title="Chart 1",
            has_map_tab=False,
            max_time=None,
            min_time=None,
            default_tab=None,
            is_published=False,
            single_year_data=False,
            len_years=None,
            has_timeline=False,
            template_id=10,
            template_title="Template 1",
        )
        chart_without_template = OwidChartRecord(
            chart_id=2,
            slug="chart2",
            title="Chart 2",
            has_map_tab=False,
            max_time=None,
            min_time=None,
            default_tab=None,
            is_published=False,
            single_year_data=False,
            len_years=None,
            has_timeline=False,
        )
        mock_service.list_charts.return_value = [chart_with_template, chart_without_template]

        response = flask_client.get("/admin/owid-charts?template=has_template")

        assert response.status_code == 200

    def test_dashboard_filter_no_template(self, owid_charts_admin_client):
        """Test dashboard filters charts without templates."""
        flask_client, mock_service = owid_charts_admin_client
        chart_without_template = OwidChartRecord(
            chart_id=2,
            slug="chart2",
            title="Chart 2",
            has_map_tab=False,
            max_time=None,
            min_time=None,
            default_tab=None,
            is_published=False,
            single_year_data=False,
            len_years=None,
            has_timeline=False,
        )
        mock_service.list_charts.return_value = [chart_without_template]

        response = flask_client.get("/admin/owid-charts?template=no_template")

        assert response.status_code == 200


class TestAddChartPopup:
    """Tests for the add chart popup route."""

    def test_add_chart_popup_renders(self, owid_charts_admin_client):
        """Test add chart popup renders."""
        flask_client, _ = owid_charts_admin_client

        response = flask_client.get("/admin/owid-charts/add")

        assert response.status_code == 200


class TestAddChart:
    """Tests for the add chart POST route."""

    def test_add_chart_success(self, owid_charts_admin_client, sample_chart_record):
        """Test adding a chart successfully."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.add_chart.return_value = sample_chart_record

        response = flask_client.post(
            "/admin/owid-charts/add",
            data={
                "slug": "new-chart",
                "title": "New Chart",
                "has_map_tab": "on",
                "is_published": "on",
            },
            follow_redirects=True,
        )

        mock_service.add_chart.assert_called_once()
        assert response.status_code == 200

    def test_add_chart_missing_slug(self, owid_charts_admin_client):
        """Test adding a chart without slug redirects with flash."""
        flask_client, mock_service = owid_charts_admin_client

        response = flask_client.post(
            "/admin/owid-charts/add",
            data={
                "slug": "",
                "title": "New Chart",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        mock_service.add_chart.assert_not_called()

    def test_add_chart_missing_title(self, owid_charts_admin_client):
        """Test adding a chart without title redirects with flash."""
        flask_client, _ = owid_charts_admin_client

        response = flask_client.post(
            "/admin/owid-charts/add",
            data={
                "slug": "new-chart",
                "title": "",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

    def test_add_chart_service_error(self, owid_charts_admin_client):
        """Test adding a chart when service raises ValueError."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.add_chart.side_effect = ValueError("Slug already exists")

        response = flask_client.post(
            "/admin/owid-charts/add",
            data={
                "slug": "existing",
                "title": "Existing Chart",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

    def test_add_chart_with_all_options(self, owid_charts_admin_client, sample_chart_record):
        """Test adding a chart with all options set."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.add_chart.return_value = sample_chart_record

        response = flask_client.post(
            "/admin/owid-charts/add",
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

        call_kwargs = mock_service.add_chart.call_args[1]
        assert call_kwargs["has_map_tab"] is True
        assert call_kwargs["max_time"] == 2024
        assert call_kwargs["min_time"] == 2000
        assert call_kwargs["default_tab"] == "table"
        assert call_kwargs["is_published"] is True
        assert call_kwargs["single_year_data"] is True
        assert call_kwargs["len_years"] == 25
        assert call_kwargs["has_timeline"] is True


class TestUpdateChart:
    """Tests for the update chart POST route."""

    def test_update_chart_success(self, owid_charts_admin_client, sample_chart_record):
        """Test updating a chart successfully."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.update_chart.return_value = sample_chart_record

        response = flask_client.post(
            "/admin/owid-charts/update",
            data={
                "chart_id": "1",
                "slug": "updated-chart",
                "title": "Updated Chart",
            },
            follow_redirects=True,
        )

        mock_service.update_chart.assert_called_once()
        assert response.status_code == 200

    def test_update_chart_missing_id(self, owid_charts_admin_client):
        """Test updating without chart_id redirects."""
        flask_client, _ = owid_charts_admin_client

        response = flask_client.post(
            "/admin/owid-charts/update",
            data={
                "slug": "updated",
                "title": "Updated",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

    def test_update_chart_missing_slug(self, owid_charts_admin_client):
        """Test updating without slug redirects with flash."""
        flask_client, _ = owid_charts_admin_client

        response = flask_client.post(
            "/admin/owid-charts/update",
            data={
                "chart_id": "1",
                "slug": "",
                "title": "Updated",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

    def test_update_chart_from_popup(self, owid_charts_admin_client, sample_chart_record):
        """Test updating a chart from popup renders popup action."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.update_chart.return_value = sample_chart_record

        response = flask_client.post(
            "/admin/owid-charts/update",
            data={
                "chart_id": "1",
                "slug": "updated",
                "title": "Updated",
                "from_popup": "1",
            },
        )

        assert response.status_code == 200

    def test_update_chart_not_found(self, owid_charts_admin_client):
        """Test updating a non-existent chart shows error."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.update_chart.side_effect = LookupError("Chart not found")

        response = flask_client.post(
            "/admin/owid-charts/update",
            data={
                "chart_id": "999",
                "slug": "missing",
                "title": "Missing",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200


class TestDeleteChart:
    """Tests for the delete chart POST route."""

    def test_delete_chart_success(self, owid_charts_admin_client, sample_chart_record):
        """Test deleting a chart successfully."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.delete_chart.return_value = sample_chart_record

        response = flask_client.post("/admin/owid-charts/1/delete", follow_redirects=True)

        mock_service.delete_chart.assert_called_once_with(1)
        assert response.status_code == 200

    def test_delete_chart_not_found(self, owid_charts_admin_client):
        """Test deleting a non-existent chart shows error."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.delete_chart.side_effect = LookupError("Chart not found")

        response = flask_client.post("/admin/owid-charts/999/delete", follow_redirects=True)

        assert response.status_code == 200

    def test_delete_chart_from_popup(self, owid_charts_admin_client, sample_chart_record):
        """Test deleting a chart from popup renders popup action."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.delete_chart.return_value = sample_chart_record

        response = flask_client.post(
            "/admin/owid-charts/1/delete",
            data={
                "from_popup": "1",
            },
        )

        assert response.status_code == 200


class TestEditChart:
    """Tests for the edit chart GET route."""

    def test_edit_chart_success(self, owid_charts_admin_client, sample_chart_record):
        """Test editing a chart renders edit page."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.get_chart.return_value = sample_chart_record

        response = flask_client.get("/admin/owid-charts/1/edit")

        assert response.status_code == 200

    def test_edit_chart_not_found(self, owid_charts_admin_client):
        """Test editing a non-existent chart shows error."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.get_chart.side_effect = LookupError("Not found")

        response = flask_client.get("/admin/owid-charts/999/edit")

        assert response.status_code == 200


class TestDownloadJson:
    """Tests for the download JSON route."""

    def test_download_json_success(self, owid_charts_admin_client, sample_chart_record):
        """Test downloading charts as JSON."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.list_charts.return_value = [sample_chart_record]

        response = flask_client.get("/admin/owid-charts/download-json")

        assert response.status_code == 200
        assert response.content_type == "application/json"
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]["slug"] == "test-chart"

    def test_download_json_no_charts(self, owid_charts_admin_client):
        """Test downloading JSON when no charts exist redirects."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.list_charts.return_value = []

        response = flask_client.get("/admin/owid-charts/download-json", follow_redirects=True)

        assert response.status_code == 200

    def test_download_json_multiple_charts(self, owid_charts_admin_client):
        """Test downloading multiple charts as JSON."""
        flask_client, mock_service = owid_charts_admin_client
        charts = [
            OwidChartRecord(
                chart_id=i,
                slug=f"chart-{i}",
                title=f"Chart {i}",
                has_map_tab=False,
                max_time=None,
                min_time=None,
                default_tab=None,
                is_published=False,
                single_year_data=False,
                len_years=None,
                has_timeline=False,
            )
            for i in range(1, 4)
        ]
        mock_service.list_charts.return_value = charts

        response = flask_client.get("/admin/owid-charts/download-json")

        data = json.loads(response.data)
        assert len(data) == 3
        assert data[0]["slug"] == "chart-1"
        assert data[2]["slug"] == "chart-3"

    def test_download_json_includes_all_fields(self, owid_charts_admin_client, sample_chart_record):
        """Test that JSON export includes all chart fields."""
        flask_client, mock_service = owid_charts_admin_client
        mock_service.list_charts.return_value = [sample_chart_record]

        response = flask_client.get("/admin/owid-charts/download-json")

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
            "template_id",
            "template_title",
            "template_source",
        ]
        for field in expected_fields:
            assert field in data
