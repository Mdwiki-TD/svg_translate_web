"""Tests for src.main_app.admin.routes.owid_charts.py"""

from __future__ import annotations

import json
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.main_app import create_app
from src.main_app.config import TestingConfig
from src.main_app.db.models import OwidChartRecord


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


def _unwrap_admin_required(view_func):
    """Unwrap the @admin_required decorator to reach the original closure."""
    return view_func.__wrapped__


def _patch_owid_charts_instance(flask_app, mock_service):
    """Find the OwidChartsRoutes instance and replace its service with the mock."""
    endpoint = "adminpanel.owidcharts.add_chart"
    view_func = flask_app.view_functions[endpoint]
    inner_func = _unwrap_admin_required(view_func)

    owid_charts_instance = inner_func.__self__
    owid_charts_instance.owid_charts_service = mock_service


@pytest.fixture
def owid_charts_admin_client(monkeypatch: pytest.MonkeyPatch, mock_service):
    """Return a configured Flask test client with mocked OWID charts service."""
    admin_user = SimpleNamespace(username="admin_user", is_active_admin=True)

    def fake_current_user():
        return admin_user

    monkeypatch.setenv("FLASK_SECRET_KEY", "testing-secret")
    monkeypatch.setattr("src.main_app.public.auth.utils.load_user", fake_current_user)
    monkeypatch.setattr("src.main_app.admin.decorators.load_user", fake_current_user)

    flask_app = create_app(TestingConfig)
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    _patch_owid_charts_instance(flask_app, mock_service)

    monkeypatch.setattr(
        "src.main_app.admin.routes.owid_charts.list_owid_charts_templates",
        MagicMock(return_value=[]),
    )
    monkeypatch.setattr(
        "src.main_app.admin.routes.owid_charts.OwidChartsService.delete",
        mock_service.delete_chart,
    )

    yield flask_app.test_client()


@pytest.fixture
def mock_service():
    """Return mock service objects for OWID charts."""
    mocks = MagicMock()
    mocks.list_charts = MagicMock(return_value=[])
    mocks.add_chart = MagicMock()
    mocks.update_chart_data = MagicMock()
    mocks.delete_chart = MagicMock()
    mocks.get_chart_by_id = MagicMock()
    return mocks


class TestOwidChartsDashboard:
    """Tests for the OWID charts dashboard route."""

    def test_dashboard_renders_with_no_charts(self, mock_service, owid_charts_admin_client):
        """Test dashboard renders when no charts exist."""

        mock_service.list_charts.return_value = []

        response = owid_charts_admin_client.get("/adminpanel/owidcharts")

        assert response.status_code == 200

    def test_dashboard_renders_with_charts(self, mock_service, owid_charts_admin_client, sample_chart_record):
        """Test dashboard renders with charts."""

        mock_service.list_charts.return_value = [sample_chart_record]

        response = owid_charts_admin_client.get("/adminpanel/owidcharts")

        assert response.status_code == 200

    def test_dashboard_filter_has_template(self, mock_service, owid_charts_admin_client):
        """Test dashboard filters charts with templates."""

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

        response = owid_charts_admin_client.get("/adminpanel/owidcharts?template=has_template")

        assert response.status_code == 200

    def test_dashboard_filter_no_template(self, mock_service, owid_charts_admin_client):
        """Test dashboard filters charts without templates."""

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

        response = owid_charts_admin_client.get("/adminpanel/owidcharts?template=no_template")

        assert response.status_code == 200


class TestAddChartPopup:
    """Tests for the add chart popup route."""

    def test_add_chart_popup_renders(self, mock_service, owid_charts_admin_client):
        """Test add chart popup renders."""

        response = owid_charts_admin_client.get("/adminpanel/owidcharts/add")

        assert response.status_code == 200


class TestAddChart:
    """Tests for the add chart POST route."""

    def test_add_chart_success(self, mock_service, owid_charts_admin_client, sample_chart_record):
        """Test adding a chart successfully."""

        mock_service.add_chart.return_value = sample_chart_record

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

        mock_service.add_chart.assert_called_once()
        assert response.status_code == 200

    def test_add_chart_missing_slug(self, mock_service, owid_charts_admin_client):
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
        mock_service.add_chart.assert_not_called()

    def test_add_chart_missing_title(self, mock_service, owid_charts_admin_client):
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

    def test_add_chart_service_error(self, mock_service, owid_charts_admin_client):
        """Test adding a chart when service raises ValueError."""

        mock_service.add_chart.side_effect = ValueError("Slug already exists")

        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/add",
            data={
                "slug": "existing",
                "title": "Existing Chart",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

    def test_add_chart_with_all_options(self, mock_service, owid_charts_admin_client, sample_chart_record):
        """Test adding a chart with all options set."""

        mock_service.add_chart.return_value = sample_chart_record

        _response = owid_charts_admin_client.post(
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

        call_kwargs = mock_service.add_chart.call_args[1]
        assert call_kwargs["has_map_tab"] == 1
        assert call_kwargs["max_time"] == 2024
        assert call_kwargs["min_time"] == 2000
        assert call_kwargs["default_tab"] == "table"
        assert call_kwargs["is_published"] == 1
        assert call_kwargs["single_year_data"] == 1
        assert call_kwargs["len_years"] == 25
        assert call_kwargs["has_timeline"] == 1


class TestUpdateChart:
    """Tests for the update chart POST route."""

    def test_update_chart_success(self, mock_service, owid_charts_admin_client, sample_chart_record):
        """Test updating a chart successfully."""

        mock_service.update_chart_data.return_value = sample_chart_record

        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/update",
            data={
                "chart_id": "1",
                "slug": "updated-chart",
                "title": "Updated Chart",
            },
            follow_redirects=True,
        )

        mock_service.update_chart_data.assert_called_once()
        assert response.status_code == 200

    def test_update_chart_missing_id(self, mock_service, owid_charts_admin_client):
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

    def test_update_chart_missing_slug(self, mock_service, owid_charts_admin_client):
        """Test updating without slug redirects with flash."""

        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/update",
            data={
                "chart_id": "1",
                "slug": "",
                "title": "updated",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

    def test_update_chart_from_popup(self, mock_service, owid_charts_admin_client, sample_chart_record):
        """Test updating a chart from popup renders popup action."""

        mock_service.update_chart_data.return_value = sample_chart_record

        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/update",
            data={
                "chart_id": "1",
                "slug": "updated",
                "title": "updated",
                "from_popup": "1",
            },
        )

        assert response.status_code == 200

    def test_update_chart_not_found(self, mock_service, owid_charts_admin_client):
        """Test updating a non-existent chart shows error."""

        mock_service.update_chart_data.side_effect = LookupError("Chart not found")

        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/update",
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

    def test_delete_chart_success(self, mock_service, owid_charts_admin_client, sample_chart_record):
        """Test deleting a chart successfully."""

        mock_service.delete.return_value = True

        response = owid_charts_admin_client.post("/adminpanel/owidcharts/1/delete", follow_redirects=True)

        mock_service.delete.assert_called_once_with(1)
        assert response.status_code == 200

    def test_delete_chart_not_found(self, mock_service, owid_charts_admin_client):
        """Test deleting a non-existent chart shows error."""

        mock_service.delete_chart.return_value = False

        response = owid_charts_admin_client.post("/adminpanel/owidcharts/999/delete", follow_redirects=True)

        assert response.status_code == 200

    def test_delete_chart_from_popup(self, mock_service, owid_charts_admin_client, sample_chart_record):
        """Test deleting a chart from popup renders popup action."""

        mock_service.delete_chart.return_value = True

        response = owid_charts_admin_client.post(
            "/adminpanel/owidcharts/1/delete",
            data={
                "from_popup": "1",
            },
        )

        assert response.status_code == 200


class TestEditChart:
    """Tests for the edit chart GET route."""

    def test_edit_chart_success(self, mock_service, owid_charts_admin_client, sample_chart_record):
        """Test editing a chart renders edit page."""

        mock_service.get_chart_by_id.return_value = sample_chart_record

        response = owid_charts_admin_client.get("/adminpanel/owidcharts/1/edit")

        assert response.status_code == 200


class TestDownloadJson:
    """Tests for the download JSON route."""

    def test_download_json_success(self, mock_service, owid_charts_admin_client, sample_chart_record):
        """Test downloading charts as JSON."""

        mock_service.list_charts.return_value = [sample_chart_record]

        response = owid_charts_admin_client.get("/adminpanel/owidcharts/download-json")

        assert response.status_code == 200
        assert response.content_type == "application/json"
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]["slug"] == "test-chart"

    def test_download_json_no_charts(self, mock_service, owid_charts_admin_client):
        """Test downloading JSON when no charts exist redirects."""

        mock_service.list_charts.return_value = []

        response = owid_charts_admin_client.get("/adminpanel/owidcharts/download-json", follow_redirects=True)

        assert response.status_code == 200

    def test_download_json_multiple_charts(self, mock_service, owid_charts_admin_client):
        """Test downloading multiple charts as JSON."""

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

        response = owid_charts_admin_client.get("/adminpanel/owidcharts/download-json")

        data = json.loads(response.data)
        assert len(data) == 3
        assert data[0]["slug"] == "chart-1"
        assert data[2]["slug"] == "chart-3"

    def test_download_json_includes_all_fields(self, mock_service, owid_charts_admin_client, sample_chart_record):
        """Test that JSON export includes all chart fields."""

        mock_service.list_charts.return_value = [sample_chart_record]

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
