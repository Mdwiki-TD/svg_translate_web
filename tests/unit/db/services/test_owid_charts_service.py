"""
Tests for src.main_app.db.services.owid_charts_service.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.db.services.owid_charts_service import (
    OwidChartsService,
    add_chart,
    count_charts,
    get_chart_by_id,
    get_chart_by_slug,
    list_charts,
    list_published_charts,
    update_chart_data,
)


def delete_chart(id: int) -> bool:
    return OwidChartsService().delete(id)

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


def _mock_query_for_read(monkeypatch, **kwargs):
    """Set up a chained mock query on the service module's db.session.query.

    Keyword args become return_value overrides on the mock query, e.g.
    first=None, all=[], or filter=mock_query (to continue chaining).
    """
    mock_query = MagicMock()
    mock_query.order_by.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.limit.return_value = mock_query
    for attr, value in kwargs.items():
        setattr(mock_query, attr, value)
    monkeypatch.setattr(
        "src.main_app.db.services.owid_charts_service.db.session.query",
        lambda cls: mock_query,
    )
    return mock_query


class TestCountCharts:
    """Tests for count_charts function."""

    def test_returns_count(self, monkeypatch):
        """Return the total number of charts."""
        _mock_query_for_read(monkeypatch, scalar=MagicMock(return_value=42))
        assert count_charts() == 42


class TestListCharts:
    """Tests for list_charts function."""

    def test_returns_all_charts(self, monkeypatch):
        """Return all charts when no limit is specified."""
        expected = [MagicMock(chart_id=1, slug="a"), MagicMock(chart_id=2, slug="b")]
        _mock_query_for_read(monkeypatch, all=MagicMock(return_value=expected))
        result = list_charts()
        assert result == expected

    def test_respects_limit(self, monkeypatch):
        """Pass the limit argument through to the query."""
        expected = [MagicMock(chart_id=1)]
        mock_query = _mock_query_for_read(monkeypatch, all=MagicMock(return_value=expected))
        result = list_charts(limit=1)
        assert result == expected
        mock_query.limit.assert_called_once_with(1)

    def test_no_limit_when_none(self, monkeypatch):
        """Do not call .limit() when limit is None."""
        mock_query = _mock_query_for_read(monkeypatch, all=MagicMock(return_value=[]))
        list_charts()
        mock_query.limit.assert_not_called()

    def test_returns_empty_list(self, monkeypatch):
        """Return empty list when no charts exist."""
        _mock_query_for_read(monkeypatch, all=MagicMock(return_value=[]))
        assert list_charts() == []


class TestListPublishedCharts:
    """Tests for list_published_charts function."""

    def test_returns_only_published(self, monkeypatch):
        """Return only charts where is_published is True."""
        expected = [MagicMock(chart_id=1, is_published=True)]
        _mock_query_for_read(monkeypatch, all=MagicMock(return_value=expected))
        result = list_published_charts()
        assert result == expected

    def test_applies_filter(self, monkeypatch):
        """Verify the filter is applied to the query."""
        mock_query = _mock_query_for_read(monkeypatch, all=MagicMock(return_value=[]))
        list_published_charts()
        mock_query.filter.assert_called_once()

    def test_returns_empty_when_none_published(self, monkeypatch):
        """Return empty list when no published charts exist."""
        _mock_query_for_read(monkeypatch, all=MagicMock(return_value=[]))
        assert list_published_charts() == []


class TestGetChart:
    """Tests for get_chart_by_id function."""

    def test_returns_chart_by_id(self, monkeypatch):
        """Return the chart when the ID exists."""
        expected = MagicMock(chart_id=1, slug="test-chart")
        _mock_query_for_read(monkeypatch, first=MagicMock(return_value=expected))
        result = get_chart_by_id(1)
        assert result is expected

    def test_returns_none_for_missing_id(self, monkeypatch):
        """Return None when no chart matches the given ID."""
        _mock_query_for_read(monkeypatch, first=MagicMock(return_value=None))
        assert get_chart_by_id(999) is None


class TestGetChartBySlug:
    """Tests for get_chart_by_slug function."""

    def test_returns_chart_by_slug(self, monkeypatch):
        """Return the chart when the slug exists."""
        expected = MagicMock(slug="existing-chart", chart_id=5)
        _mock_query_for_read(monkeypatch, first=MagicMock(return_value=expected))
        result = get_chart_by_slug("existing-chart")
        assert result is expected

    def test_returns_none_for_missing_slug(self, monkeypatch):
        """Return None when no chart matches the given slug."""
        _mock_query_for_read(monkeypatch, first=MagicMock(return_value=None))
        assert get_chart_by_slug("nonexistent") is None


class TestAddChart:
    """Tests for add_chart function."""

    def test_creates_chart_with_valid_data(self, monkeypatch):
        """Create a chart record with valid keyword arguments."""
        mock_db = MagicMock()
        monkeypatch.setattr("src.main_app.db.services.owid_charts_service.db", mock_db)
        from src.main_app.db.models import OwidChartRecord

        result = add_chart(chart_id=1, slug="test-chart", title="Test Chart")
        assert isinstance(result, OwidChartRecord)
        assert result.chart_id == 1
        assert result.slug == "test-chart"
        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()
        mock_db.session.refresh.assert_called_once()

    def test_filters_out_none_values(self, monkeypatch):
        """Exclude None values from chart creation data."""
        mock_db = MagicMock()
        monkeypatch.setattr("src.main_app.db.services.owid_charts_service.db", mock_db)

        result = add_chart(chart_id=1, slug="test-chart", title=None, max_time=None)
        assert result.chart_id == 1
        assert result.slug == "test-chart"

    def test_filters_out_non_existent_attributes(self, monkeypatch):
        """Exclude unknown attributes from chart creation data."""
        mock_db = MagicMock()
        monkeypatch.setattr("src.main_app.db.services.owid_charts_service.db", mock_db)

        result = add_chart(chart_id=1, slug="test", invalid_attr="value")
        assert result.chart_id == 1
        assert result.slug == "test"


class TestUpdateChartData:
    """Tests for update_chart_data function."""

    def test_updates_chart_fields(self, monkeypatch):
        """Update existing chart fields with provided data."""
        mock_record = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_record
        mock_db = MagicMock()
        mock_db.session.query.return_value = mock_query
        monkeypatch.setattr("src.main_app.db.services.owid_charts_service.db", mock_db)

        result = update_chart_data(1, {"title": "Updated"})
        assert result is not None
        assert result.title == "Updated"
        mock_db.session.commit.assert_called_once()
        mock_db.session.refresh.assert_called_once_with(mock_record)

    def test_returns_none_for_missing_chart(self, monkeypatch):
        """Return None when chart ID does not exist."""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db = MagicMock()
        mock_db.session.query.return_value = mock_query
        monkeypatch.setattr("src.main_app.db.services.owid_charts_service.db", mock_db)

        result = update_chart_data(999, {"title": "Updated"})
        assert result is None
        mock_db.session.commit.assert_not_called()

    def test_ignores_none_values(self, monkeypatch):
        """Ignore None values in update data."""
        mock_record = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_record
        mock_db = MagicMock()
        mock_db.session.query.return_value = mock_query
        monkeypatch.setattr("src.main_app.db.services.owid_charts_service.db", mock_db)

        result = update_chart_data(1, {"title": "New", "max_time": None})
        assert result is not None
        assert result.title == "New"

    def test_ignores_non_existent_attributes(self, monkeypatch):
        """Ignore unknown attributes in update data."""
        mock_record = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_record
        mock_db = MagicMock()
        mock_db.session.query.return_value = mock_query
        monkeypatch.setattr("src.main_app.db.services.owid_charts_service.db", mock_db)

        result = update_chart_data(1, {"title": "New", "invalid_attr": "value"})
        assert result is not None
        assert result.title == "New"


class TestDeleteChart:
    """Tests for delete_chart function."""

    def test_deletes_chart(self, monkeypatch):
        """Delete an existing chart and return True."""
        mock_record = MagicMock()
        mock_db = MagicMock()
        mock_db.session.get.return_value = mock_record
        monkeypatch.setattr("src.main_app.db.services.delete_service.db", mock_db)

        result = delete_chart(1)
        assert result is True
        mock_db.session.get.assert_called_once()
        mock_db.session.delete.assert_called_once_with(mock_record)
        mock_db.session.commit.assert_called_once()

    def test_returns_false_for_missing_chart(self, monkeypatch):
        """Return False when chart ID does not exist."""
        mock_db = MagicMock()
        mock_db.session.get.return_value = None
        monkeypatch.setattr("src.main_app.db.services.delete_service.db", mock_db)

        result = delete_chart(999)
        assert result is False
        mock_db.session.get.assert_called_once()
        mock_db.session.delete.assert_not_called()

    def test_returns_false_for_none_id(self, monkeypatch):
        """Return False when chart ID is None."""
        mock_db = MagicMock()
        monkeypatch.setattr("src.main_app.db.services.delete_service.db", mock_db)

        result = delete_chart(None)
        assert result is False
        mock_db.session.get.assert_not_called()
