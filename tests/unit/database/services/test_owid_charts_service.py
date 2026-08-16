"""Tests for owid_charts_service module."""

from __future__ import annotations

import pytest

from src.main_app.database.services import OwidChartsService, TemplateService


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = OwidChartsService()
        self.templates_service = TemplateService()


class TestCountCharts(TestSetup):
    """Tests for count_charts function."""

    def test_returns_count(self) -> None:
        """Return the total number of charts."""
        self.service.create(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)
        self.service.create(slug="test-chart1", title="Test Chart1", is_published=True, max_time=2025)

        assert self.service.count_charts() == 2


class TestListCharts(TestSetup):
    """Tests for list_charts function."""

    def test_returns_all_charts(self) -> None:
        """Return all charts when no limit is specified."""
        chart_record = self.service.create(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)

        result = self.service.list_charts()
        assert len(result) == 1
        assert result[0].chart_id == chart_record.chart_id
        assert result[0].slug == chart_record.slug

    def test_respects_limit(self) -> None:
        """Apply the limit argument to the query."""
        chart_record = self.service.create(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)
        second = self.service.create(slug="second-chart", title="Second Chart")

        result = self.service.list_charts(limit=1)
        assert len(result) == 1
        assert result[0].chart_id == chart_record.chart_id

    def test_returns_empty_list(self) -> None:
        """Return empty list when no charts exist."""
        assert self.service.list_charts() == []


class TestListPublishedCharts(TestSetup):
    """Tests for list_published_charts function."""

    def test_returns_only_published(self) -> None:
        """Return only charts where is_published is True."""
        chart_record = self.service.create(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)

        unpublished = self.service.create(slug="unpublished", title="Unpublished", is_published=False)

        result = self.service.list_published_charts()
        assert len(result) == 1
        assert result[0].chart_id == chart_record.chart_id
        assert result[0].is_published is True

    def test_returns_empty_when_none_published(self) -> None:
        """Return empty list when no published charts exist."""
        self.service.create(slug="unpublished", title="Unpublished", is_published=False)

        assert self.service.list_published_charts() == []


class TestGetChart(TestSetup):
    """Tests for get_chart_by_id function."""

    def test_returns_chart_by_id(self) -> None:
        """Return the chart when the ID exists."""
        chart_record = self.service.create(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)

        result = self.service.get_chart_by_id(chart_record.chart_id)
        assert result is not None
        assert result.chart_id == chart_record.chart_id

    def test_returns_none_for_missing_id(self) -> None:
        """Return None when no chart matches the given ID."""
        assert self.service.get_chart_by_id(999) is None


class TestGetChartBySlug(TestSetup):
    """Tests for get_chart_by_slug function."""

    def test_returns_chart_by_slug(self) -> None:
        """Return the chart when the slug exists."""
        chart_record = self.service.create(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)

        result = self.service.get_chart_by_slug(chart_record.slug)
        assert result is not None
        assert result.chart_id == chart_record.chart_id

    def test_returns_none_for_missing_slug(self) -> None:
        """Return None when no chart matches the given slug."""
        assert self.service.get_chart_by_slug("nonexistent") is None

    def test_returns_persisted_source_citation(self) -> None:
        """Return the complete source citation saved for the chart."""
        source = "Food and Agriculture Organization of the United Nations (2025) – with major processing by Our World in Data"
        self.service.create(slug="wheat-production", title="Wheat production", source=source)

        result = self.service.get_chart_by_slug("wheat-production")

        assert result is not None
        assert result.source == source


class TestAddChart(TestSetup):
    """Tests for add_chart function."""

    def test_creates_chart_with_valid_data(self) -> None:
        """Create a chart record with valid keyword arguments."""
        result = self.service.add_chart(slug="test-chart", title="Test Chart")

        assert result is not None
        assert result.chart_id is not None
        assert result.slug == "test-chart"
        assert self.service.get(result.chart_id) is not None

    def test_filters_out_none_values(self) -> None:
        """Exclude None values from chart creation data and fail if required fields are missing."""
        result = self.service.add_chart(slug="test-chart", title=None, max_time=None)
        assert result is None

    def test_filters_out_non_existent_attributes(self) -> None:
        """Exclude unknown attributes from chart creation data."""
        result = self.service.add_chart(slug="test", title="Test", invalid_attr="value")
        assert result is not None
        assert result.slug == "test"
        assert not hasattr(result, "invalid_attr")


class TestUpdateChartData(TestSetup):
    """Tests for update_chart_data function."""

    def test_updates_chart_fields(self) -> None:
        """Update existing chart fields with provided data."""
        chart_record = self.service.create(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)

        result = self.service.update_chart_data(chart_record.chart_id, {"title": "Updated"})

        assert result is not None
        assert result.title == "Updated"
        persisted = self.service.get(chart_record.chart_id)
        assert persisted is not None
        assert persisted.title == "Updated"

    def test_returns_none_for_missing_chart(self) -> None:
        """Return None when chart ID does not exist."""
        result = self.service.update_chart_data(999, {"title": "Updated"})
        assert result is None

    def test_updates_persisted_source_citation(self) -> None:
        """Persist the refreshed OWID citation for later crop-job lookup."""
        chart_record = self.service.create(slug="wheat-production", title="Wheat production", source="")
        source = "Food and Agriculture Organization of the United Nations (2025) – with major processing by Our World in Data"

        result = self.service.update_chart_data(chart_record.chart_id, {"source": source})
        persisted = self.service.get_chart_by_slug("wheat-production")

        assert result is not None
        assert result.source == source
        assert persisted is not None
        assert persisted.source == source

    def test_ignores_none_values(self) -> None:
        """Ignore None values in update data."""
        chart_record = self.service.create(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)

        result = self.service.update_chart_data(chart_record.chart_id, {"title": "New", "max_time": None})
        assert result is not None
        assert result.title == "New"
        assert result.max_time == 2024

    def test_ignores_non_existent_attributes(self) -> None:
        """Ignore unknown attributes in update data."""
        chart_record = self.service.create(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)

        result = self.service.update_chart_data(chart_record.chart_id, {"title": "New", "invalid_attr": "value"})
        assert result is not None
        assert result.title == "New"
        assert not hasattr(result, "invalid_attr")


class TestDeleteChart(TestSetup):
    """Tests for delete_chart function."""

    def test_deletes_chart(self) -> None:
        """Delete an existing chart and return True."""
        chart_record = self.service.create(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)

        result = self.service.delete(chart_record.chart_id)
        assert result is True
        assert self.service.get(chart_record.chart_id) is None

    def test_returns_false_for_missing_chart(self) -> None:
        """Return False when chart ID does not exist."""
        result = self.service.delete(999)
        assert result is False

    def test_returns_false_for_none_id(self) -> None:
        """Return False when chart ID is None."""
        result = self.service.delete(None)
        assert result is False
