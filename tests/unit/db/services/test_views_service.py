from __future__ import annotations

import pytest

from src.main_app.db.models.owid_charts import OwidChartRecord
from src.main_app.db.models.templates import TemplateRecord
from src.main_app.db.services.views_service import ViewsService
from src.main_app.extensions import db


@pytest.fixture(autouse=True)
def sqlite_view_functions() -> None:
    """Register MySQL-compatible functions used by views for SQLite tests."""
    raw_connection = db.engine.raw_connection()
    raw_connection.create_function("now", 0, lambda: "2026-01-01")
    raw_connection.create_function("YEAR", 1, lambda value: int(str(value)[:4]))
    raw_connection.close()


@pytest.fixture
def chart_template_records() -> tuple[OwidChartRecord, TemplateRecord]:
    chart = OwidChartRecord(slug="chart-a", title="Chart A", max_time=2024, owid_variable_id=123)
    template = TemplateRecord(title="Template A", slug="chart-a", last_world_year=2023, source="owid")
    db.session.add_all([chart, template])
    db.session.commit()
    db.session.refresh(chart)
    db.session.refresh(template)
    return chart, template


class TestViewsService:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = ViewsService()

    def test_list_templates_need_update_returns_records(
        self, chart_template_records: tuple[OwidChartRecord, TemplateRecord]
    ) -> None:
        chart, template = chart_template_records

        result = self.service.list_templates_need_update()

        assert len(result) == 1
        assert result[0].template_id == template.id
        assert result[0].template_title == template.title
        assert result[0].slug == chart.slug

    def test_list_templates_need_update_returns_empty_list(self) -> None:
        assert self.service.list_templates_need_update() == []

    def test_list_owid_charts_templates_returns_records(
        self, chart_template_records: tuple[OwidChartRecord, TemplateRecord]
    ) -> None:
        chart, template = chart_template_records

        result = self.service.list_owid_charts_templates()

        assert len(result) == 1
        assert result[0].chart_id == chart.chart_id
        assert result[0].template_id == template.id
        assert result[0].template_title == template.title

    def test_list_owid_charts_templates_returns_empty_list(self) -> None:
        assert self.service.list_owid_charts_templates() == []
