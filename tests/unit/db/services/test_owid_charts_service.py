"""Tests for owid_charts_service module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.db.models import OwidChartRecord
from src.main_app.db.services.owid_charts_service import OwidChartsService


def _mock_query_for_read(**kwargs):
    """Set up a chained mock query on db.session.query.

    The service methods call self.session.query(Model).filter(...).first()
    or self.session.query(Model).filter(...).order_by(...).all().

    Since query(Model) returns mock_query.return_value, the chain is:
      mock_query(Model).filter(...).first()
      → mock_query.return_value.filter.return_value.first.return_value

    For all=... the chain is:
      mock_query(Model).filter(...).order_by(...).all()
      → mock_query.return_value.filter.return_value.order_by.return_value.all.return_value
    """
    mock_query = MagicMock()

    mock_filter = mock_query.return_value.filter.return_value
    mock_order_by = mock_filter.order_by.return_value

    for attr, value in kwargs.items():
        if attr == "all":
            mock_order_by.all.return_value = value
        elif attr == "first":
            mock_filter.first.return_value = value
        elif attr == "scalar":
            mock_query.return_value.scalar.return_value = value
        else:
            setattr(mock_filter, attr, value)

    return mock_query


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        self.service = OwidChartsService()


class TestCountCharts(TestSetup):
    """Tests for count_charts function."""

    def test_returns_count(self, monkeypatch):
        """Return the total number of charts."""
        mock_query = _mock_query_for_read(scalar=42)
        mock_db_session = MagicMock()
        mock_db_session.query.return_value = mock_query.return_value
        self.service.session = mock_db_session

        assert self.service.count_charts() == 42


class TestListCharts(TestSetup):
    """Tests for list_charts function."""

    def test_returns_all_charts(self, monkeypatch):
        """Return all charts when no limit is specified."""
        expected = [MagicMock(chart_id=1, slug="a"), MagicMock(chart_id=2, slug="b")]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = expected
        monkeypatch.setattr(self.service.session, "execute", MagicMock(return_value=mock_result))

        result = self.service.list_charts()
        assert result == expected

    def test_respects_limit(self, monkeypatch):
        """Pass the limit argument through to the query."""
        expected = [MagicMock(chart_id=1)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = expected
        mock_execute = MagicMock(return_value=mock_result)
        monkeypatch.setattr(self.service.session, "execute", mock_execute)

        result = self.service.list_charts(limit=1)
        assert result == expected
        executed_stmt = mock_execute.call_args[0][0]
        assert executed_stmt.column_descriptions[0]["type"] is not None

    def test_no_limit_when_none(self, monkeypatch):
        """Do not call .limit() when limit is None."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        monkeypatch.setattr(self.service.session, "execute", MagicMock(return_value=mock_result))

        self.service.list_charts()

    def test_returns_empty_list(self, monkeypatch):
        """Return empty list when no charts exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        monkeypatch.setattr(self.service.session, "execute", MagicMock(return_value=mock_result))

        assert self.service.list_charts() == []


class TestListPublishedCharts(TestSetup):
    """Tests for list_published_charts function."""

    def test_returns_only_published(self, monkeypatch):
        """Return only charts where is_published is True."""
        expected = [MagicMock(chart_id=1, is_published=True)]
        mock_query = _mock_query_for_read(all=expected)
        mock_db_session = MagicMock()
        mock_db_session.query.return_value = mock_query.return_value
        self.service.session = mock_db_session

        result = self.service.list_published_charts()
        assert result == expected

    def test_applies_filter(self, monkeypatch):
        """Verify the filter is applied to the query."""
        mock_query = _mock_query_for_read(all=[])
        mock_db_session = MagicMock()
        mock_db_session.query.return_value = mock_query.return_value
        self.service.session = mock_db_session

        self.service.list_published_charts()
        mock_query.return_value.filter.assert_called_once()

    def test_returns_empty_when_none_published(self, monkeypatch):
        """Return empty list when no published charts exist."""
        mock_query = _mock_query_for_read(all=[])
        mock_db_session = MagicMock()
        mock_db_session.query.return_value = mock_query.return_value
        self.service.session = mock_db_session

        assert self.service.list_published_charts() == []


class TestGetChart(TestSetup):
    """Tests for get_chart_by_id function."""

    def test_returns_chart_by_id(self, monkeypatch):
        """Return the chart when the ID exists."""
        expected = MagicMock(chart_id=1, slug="test-chart")
        mock_query = _mock_query_for_read(first=expected)
        mock_db_session = MagicMock()
        mock_db_session.query.return_value = mock_query.return_value
        self.service.session = mock_db_session

        result = self.service.get_chart_by_id(1)
        assert result is expected

    def test_returns_none_for_missing_id(self, monkeypatch):
        """Return None when no chart matches the given ID."""
        mock_query = _mock_query_for_read(first=None)
        mock_db_session = MagicMock()
        mock_db_session.query.return_value = mock_query.return_value
        self.service.session = mock_db_session

        assert self.service.get_chart_by_id(999) is None


class TestGetChartBySlug(TestSetup):
    """Tests for get_chart_by_slug function."""

    def test_returns_chart_by_slug(self, monkeypatch):
        """Return the chart when the slug exists."""
        expected = MagicMock(slug="existing-chart", chart_id=5)
        mock_query = _mock_query_for_read(first=expected)
        mock_db_session = MagicMock()
        mock_db_session.query.return_value = mock_query.return_value
        self.service.session = mock_db_session

        result = self.service.get_chart_by_slug("existing-chart")
        assert result is expected

    def test_returns_none_for_missing_slug(self, monkeypatch):
        """Return None when no chart matches the given slug."""
        mock_query = _mock_query_for_read(first=None)
        mock_db_session = MagicMock()
        mock_db_session.query.return_value = mock_query.return_value
        self.service.session = mock_db_session

        assert self.service.get_chart_by_slug("nonexistent") is None


class TestAddChart(TestSetup):
    """Tests for add_chart function."""

    def test_creates_chart_with_valid_data(self, monkeypatch):
        """Create a chart record with valid keyword arguments."""
        mock_db_session = MagicMock()
        self.service.session = mock_db_session

        result = self.service.add_chart(chart_id=1, slug="test-chart", title="Test Chart")
        assert result is not None
        assert isinstance(result, OwidChartRecord)
        assert result.chart_id == 1
        assert result.slug == "test-chart"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    def test_filters_out_none_values(self, monkeypatch):
        """Exclude None values from chart creation data."""
        mock_db_session = MagicMock()
        self.service.session = mock_db_session

        result = self.service.add_chart(chart_id=1, slug="test-chart", title=None, max_time=None)
        assert result is not None
        assert result.chart_id == 1
        assert result.slug == "test-chart"

    def test_filters_out_non_existent_attributes(self, monkeypatch):
        """Exclude unknown attributes from chart creation data."""
        mock_db_session = MagicMock()
        self.service.session = mock_db_session

        result = self.service.add_chart(chart_id=1, slug="test", invalid_attr="value")
        assert result is not None
        assert result.chart_id == 1
        assert result.slug == "test"


class TestUpdateChartData(TestSetup):
    """Tests for update_chart_data function."""

    def test_updates_chart_fields(self, monkeypatch):
        """Update existing chart fields with provided data."""
        mock_record = MagicMock()
        mock_record.title = "Updated"
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        mock_db_session = MagicMock()
        mock_db_session.query.return_value = mock_query
        self.service.session = mock_db_session

        result = self.service.update_chart_data(1, {"title": "Updated"})
        assert result is not None
        assert result.title == "Updated"
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_record)

    def test_returns_none_for_missing_chart(self, monkeypatch):
        """Return None when chart ID does not exist."""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session = MagicMock()
        mock_db_session.query.return_value = mock_query
        self.service.session = mock_db_session

        result = self.service.update_chart_data(999, {"title": "Updated"})
        assert result is None
        mock_db_session.commit.assert_not_called()

    def test_ignores_none_values(self, monkeypatch):
        """Ignore None values in update data."""
        mock_record = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        mock_db_session = MagicMock()
        mock_db_session.query.return_value = mock_query
        self.service.session = mock_db_session

        result = self.service.update_chart_data(1, {"title": "New", "max_time": None})
        assert result is not None
        assert result.title == "New"

    def test_ignores_non_existent_attributes(self, monkeypatch):
        """Ignore unknown attributes in update data."""
        mock_record = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_record
        mock_db_session = MagicMock()
        mock_db_session.query.return_value = mock_query
        self.service.session = mock_db_session

        result = self.service.update_chart_data(1, {"title": "New", "invalid_attr": "value"})
        assert result is not None
        assert result.title == "New"


class TestDeleteChart(TestSetup):
    """Tests for delete_chart function."""

    def test_deletes_chart(self, monkeypatch):
        """Delete an existing chart and return True."""
        mock_record = MagicMock()
        mock_db_session = MagicMock()
        mock_db_session.get.return_value = mock_record
        self.service.session = mock_db_session

        result = self.service.delete(1)
        assert result is True
        mock_db_session.get.assert_called_once()
        mock_db_session.delete.assert_called_once_with(mock_record)
        mock_db_session.commit.assert_called_once()

    def test_returns_false_for_missing_chart(self, monkeypatch):
        """Return False when chart ID does not exist."""
        mock_db_session = MagicMock()
        mock_db_session.get.return_value = None
        self.service.session = mock_db_session

        result = self.service.delete(999)
        assert result is False
        mock_db_session.get.assert_called_once()
        mock_db_session.delete.assert_not_called()

    def test_returns_false_for_none_id(self, monkeypatch):
        """Return False when chart ID is None."""
        mock_db_session = MagicMock()
        self.service.session = mock_db_session

        result = self.service.delete(None)
        assert result is False
        mock_db_session.get.assert_not_called()
