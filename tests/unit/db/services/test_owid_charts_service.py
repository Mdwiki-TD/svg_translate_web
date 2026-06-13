# ruff: noqa: F401
"""
Tests for src.main_app.db.services.owid_charts_service.
TODO: write tests
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.db.services.owid_charts_service import (
    add_chart,
    delete_chart,
    get_chart_by_id,
    get_chart_by_slug,
    list_charts,
    list_published_charts,
    update_chart_data,
)


@pytest.fixture
def sample_record():
    """Create a sample OwidChartRecord."""
    from src.main_app.db.models import OwidChartRecord

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
def mock_db_instance():
    """Create a mock OwidChartsDB instance."""
    return MagicMock()


class TestListCharts:
    """Tests for list_charts function."""


class TestListPublishedCharts:
    """Tests for list_published_charts function."""


class TestGetChart:
    """Tests for get_chart_by_id function."""


class TestGetChartBySlug:
    """Tests for get_chart_by_slug function."""


class TestAddChart:
    """Tests for add_chart function."""


class TestUpdateChartData:
    """Tests for update_chart_data function."""


class TestDeleteChart:
    """Tests for delete_chart function."""
