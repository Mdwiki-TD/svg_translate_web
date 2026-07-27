"""Tests for owid_charts_service module."""

from __future__ import annotations

import pytest

from src.main_app.db.models import OwidChartRecord, TemplateRecord
from src.main_app.db.services.owid_charts_service import OwidChartsService
from src.main_app.extensions import db


@pytest.fixture
def chart_record() -> OwidChartRecord:
    record = OwidChartRecord(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)
    db.session.add(record)
    db.session.commit()
    db.session.refresh(record)
    return record


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = OwidChartsService()


class TestCountCharts(TestSetup):
    """Tests for count_charts function."""

    def test_returns_count(self, chart_record: OwidChartRecord) -> None:
        """Return the total number of charts."""
        assert self.service.count_charts() == 1


class TestListCharts(TestSetup):
    """Tests for list_charts function."""

    def test_returns_all_charts(self, chart_record: OwidChartRecord) -> None:
        """Return all charts when no limit is specified."""
        result = self.service.list_charts()
        assert len(result) == 1
        assert result[0].chart_id == chart_record.chart_id
        assert result[0].slug == chart_record.slug

    def test_respects_limit(self, chart_record: OwidChartRecord) -> None:
        """Apply the limit argument to the query."""
        second = OwidChartRecord(slug="second-chart", title="Second Chart")
        db.session.add(second)
        db.session.commit()

        result = self.service.list_charts(limit=1)
        assert len(result) == 1
        assert result[0].chart_id == chart_record.chart_id

    def test_returns_empty_list(self) -> None:
        """Return empty list when no charts exist."""
        assert self.service.list_charts() == []


class TestListChartsWithTemplates(TestSetup):
    """Tests for list_charts_with_templates function."""

    def test_returns_charts_with_matching_template(self, chart_record: OwidChartRecord) -> None:
        template = TemplateRecord(title="Template A", slug=chart_record.slug, source="owid")
        db.session.add(template)
        db.session.commit()
        db.session.refresh(template)

        result = self.service.list_charts_with_templates()

        assert len(result) == 1
        chart, template_id, template_title = result[0]
        assert chart.chart_id == chart_record.chart_id
        assert template_id == template.id
        assert template_title == template.title

    def test_returns_chart_without_template(self, chart_record: OwidChartRecord) -> None:
        result = self.service.list_charts_with_templates()

        assert len(result) == 1
        chart, template_id, template_title = result[0]
        assert chart.chart_id == chart_record.chart_id
        assert template_id is None
        assert template_title is None


class TestListPublishedCharts(TestSetup):
    """Tests for list_published_charts function."""

    def test_returns_only_published(self, chart_record: OwidChartRecord) -> None:
        """Return only charts where is_published is True."""
        unpublished = OwidChartRecord(slug="unpublished", title="Unpublished", is_published=False)
        db.session.add(unpublished)
        db.session.commit()

        result = self.service.list_published_charts()
        assert len(result) == 1
        assert result[0].chart_id == chart_record.chart_id
        assert result[0].is_published is True

    def test_returns_empty_when_none_published(self) -> None:
        """Return empty list when no published charts exist."""
        db.session.add(OwidChartRecord(slug="unpublished", title="Unpublished", is_published=False))
        db.session.commit()

        assert self.service.list_published_charts() == []


class TestGetChart(TestSetup):
    """Tests for get_chart_by_id function."""

    def test_returns_chart_by_id(self, chart_record: OwidChartRecord) -> None:
        """Return the chart when the ID exists."""
        result = self.service.get_chart_by_id(chart_record.chart_id)
        assert result is not None
        assert result.chart_id == chart_record.chart_id

    def test_returns_none_for_missing_id(self) -> None:
        """Return None when no chart matches the given ID."""
        assert self.service.get_chart_by_id(999) is None


class TestGetChartBySlug(TestSetup):
    """Tests for get_chart_by_slug function."""

    def test_returns_chart_by_slug(self, chart_record: OwidChartRecord) -> None:
        """Return the chart when the slug exists."""
        result = self.service.get_chart_by_slug(chart_record.slug)
        assert result is not None
        assert result.chart_id == chart_record.chart_id

    def test_returns_none_for_missing_slug(self) -> None:
        """Return None when no chart matches the given slug."""
        assert self.service.get_chart_by_slug("nonexistent") is None


class TestAddChart(TestSetup):
    """Tests for add_chart function."""

    def test_creates_chart_with_valid_data(self) -> None:
        """Create a chart record with valid keyword arguments."""
        result = self.service.add_chart(slug="test-chart", title="Test Chart")

        assert result is not None
        assert result.chart_id is not None
        assert result.slug == "test-chart"
        assert db.session.get(OwidChartRecord, result.chart_id) is not None

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

    def test_updates_chart_fields(self, chart_record: OwidChartRecord) -> None:
        """Update existing chart fields with provided data."""
        result = self.service.update_chart_data(chart_record.chart_id, {"title": "Updated"})

        assert result is not None
        assert result.title == "Updated"
        persisted = db.session.get(OwidChartRecord, chart_record.chart_id)
        assert persisted is not None
        assert persisted.title == "Updated"

    def test_returns_none_for_missing_chart(self) -> None:
        """Return None when chart ID does not exist."""
        result = self.service.update_chart_data(999, {"title": "Updated"})
        assert result is None

    def test_ignores_none_values(self, chart_record: OwidChartRecord) -> None:
        """Ignore None values in update data."""
        result = self.service.update_chart_data(chart_record.chart_id, {"title": "New", "max_time": None})
        assert result is not None
        assert result.title == "New"
        assert result.max_time == 2024

    def test_ignores_non_existent_attributes(self, chart_record: OwidChartRecord) -> None:
        """Ignore unknown attributes in update data."""
        result = self.service.update_chart_data(chart_record.chart_id, {"title": "New", "invalid_attr": "value"})
        assert result is not None
        assert result.title == "New"
        assert not hasattr(result, "invalid_attr")


class TestDeleteChart(TestSetup):
    """Tests for delete_chart function."""

    def test_deletes_chart(self, chart_record: OwidChartRecord) -> None:
        """Delete an existing chart and return True."""
        result = self.service.delete(chart_record.chart_id)
        assert result is True
        assert db.session.get(OwidChartRecord, chart_record.chart_id) is None

    def test_returns_false_for_missing_chart(self) -> None:
        """Return False when chart ID does not exist."""
        result = self.service.delete(999)
        assert result is False

    def test_returns_false_for_none_id(self) -> None:
        """Return False when chart ID is None."""
        result = self.service.delete(None)
        assert result is False
