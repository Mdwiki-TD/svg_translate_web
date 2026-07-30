"""Tests for owid_charts_service module."""

from __future__ import annotations

import pytest

from src.main_app.db.models import OwidChartRecord
from src.main_app.db.services import (
    ChartAndTemplate,
    ChartsAndTemplatesService,
    OwidChartsService,
    TemplateService,
)


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = OwidChartsService()
        self.charts_and_tmps_service = ChartsAndTemplatesService()
        self.templates_service = TemplateService()


class TestListChartsWithTemplates(TestSetup):
    """Tests for list_charts_with_templates function."""

    def test_list_charts_with_templates(self) -> None:
        chart_record = self.service.create(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)

        template = self.templates_service.create(title="Template A", slug=chart_record.slug, source="owid")

        result: list[ChartAndTemplate] = self.charts_and_tmps_service.list_charts_with_templates()

        assert len(result) == 1
        x = result[0]
        assert x.chart.chart_id == chart_record.chart_id
        assert x.template_id == template.id
        assert x.template_title == template.title


class TestListChartsWithoutTemplates(TestSetup):
    """Tests for list_charts_without_templates function."""

    def test_list_charts_without_templates(self) -> None:
        chart_record = self.service.create(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)

        result: list[OwidChartRecord] = self.charts_and_tmps_service.list_charts_without_templates()

        assert len(result) == 1
        x = result[0]
        assert x.chart_id == chart_record.chart_id


class TestListAll(TestSetup):
    """Tests for list_all function."""

    def test_returns_chart_without_template(self) -> None:
        chart_record = self.service.create(slug="test-chart", title="Test Chart", is_published=True, max_time=2024)

        result: list[ChartAndTemplate] = self.charts_and_tmps_service.list_all()

        assert len(result) == 1
        x = result[0]
        assert x.chart.chart_id == chart_record.chart_id
        assert x.template_id is None
        assert x.template_title is None
