"""Tests for src.main_app.app_routes.main_routes.owid_charts_routes.py"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.main_app.shared.models import OwidChartRecord


@pytest.fixture
def sample_chart():
    """Create a sample published chart."""
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
def sample_unpublished_chart():
    """Create a sample unpublished chart."""
    return OwidChartRecord(
        chart_id=2,
        slug="draft-chart",
        title="Draft Chart",
        has_map_tab=False,
        max_time=None,
        min_time=None,
        default_tab=None,
        is_published=False,
        single_year_data=False,
        len_years=None,
        has_timeline=False,
    )


@pytest.fixture
def owid_charts_client(sample_chart, sample_unpublished_chart):
    """Create Flask test client with mocked owid_charts_service."""
    with (
        patch("src.main_app.app_routes.main_routes.owid_charts_routes.list_published_charts") as mock_published,
        patch("src.main_app.app_routes.main_routes.owid_charts_routes.list_charts") as mock_all,
    ):
        mock_published.return_value = [sample_chart]
        mock_all.return_value = [sample_chart, sample_unpublished_chart]

        from src.main_app import create_app

        flask_app = create_app()
        flask_app.config["TESTING"] = True
        flask_app.config["WTF_CSRF_ENABLED"] = False

        yield flask_app.test_client(), mock_published, mock_all


class TestIndexRoute:
    """Tests for the public charts index route."""

    def test_index_renders_with_published_charts(self, owid_charts_client):
        """Test index page renders with published charts."""
        flask_client, mock_published, _ = owid_charts_client

        response = flask_client.get("/owid-charts/")

        assert response.status_code == 200
        mock_published.assert_called_once()

    def test_index_calls_list_charts(self, owid_charts_client):
        """Test index page also calls list_charts for total count."""
        flask_client, _, mock_all = owid_charts_client

        flask_client.get("/owid-charts/")

        mock_all.assert_called_once()


class TestAllChartsRoute:
    """Tests for the all charts route."""

    def test_all_charts_renders(self, owid_charts_client):
        """Test all charts page renders."""
        flask_client, _, mock_all = owid_charts_client

        response = flask_client.get("/owid-charts/all")

        assert response.status_code == 200
        mock_all.assert_called_once()

    def test_all_charts_includes_unpublished(self, owid_charts_client, sample_unpublished_chart):
        """Test all charts page includes unpublished charts."""
        flask_client, _, mock_all = owid_charts_client
        mock_all.return_value = [sample_unpublished_chart]

        response = flask_client.get("/owid-charts/all")

        assert response.status_code == 200

    def test_all_charts_empty_list(self, owid_charts_client):
        """Test all charts page with no charts."""
        flask_client, _, mock_all = owid_charts_client
        mock_all.return_value = []

        response = flask_client.get("/owid-charts/all")

        assert response.status_code == 200
