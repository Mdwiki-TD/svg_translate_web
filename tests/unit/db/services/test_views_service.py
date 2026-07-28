from __future__ import annotations

import pytest

from src.main_app.db.models.owid_charts import OwidChartRecord
from src.main_app.db.models.templates import TemplateRecord
from src.main_app.db.services import OwidChartsService, TemplateService
from src.main_app.db.services.views_service import ViewsService


@pytest.fixture
def chart_template_records() -> tuple[OwidChartRecord, TemplateRecord]:
    chart_record = OwidChartsService().create(
        slug="chart-a",
        title="Chart A",
        max_time=2024,
        owid_variable_id=123,
    )
    template_record = TemplateService().create(
        title="Template A",
        slug="chart-a",
        last_world_year=2023,
        source="owid",
    )
    return chart_record, template_record


class TestViewsService:
    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = ViewsService()

    def test_list_templates_need_update_returns_records(
        self, chart_template_records: tuple[OwidChartRecord, TemplateRecord]
    ) -> None:
        chart_record, template_record = chart_template_records

        result = self.service.list_templates_need_update()

        assert len(result) == 1
        assert result[0].template_id == template_record.id
        assert result[0].template_title == template_record.title
        assert result[0].slug == chart_record.slug

    def test_list_templates_need_update_returns_empty_list(self) -> None:
        assert self.service.list_templates_need_update() == []

    def test_list_owid_charts_templates_returns_records(
        self, chart_template_records: tuple[OwidChartRecord, TemplateRecord]
    ) -> None:
        chart_record, template_record = chart_template_records

        result = self.service.list_owid_charts_templates()

        assert len(result) == 1
        assert result[0].chart_id == chart_record.chart_id
        assert result[0].template_id == template_record.id
        assert result[0].template_title == template_record.title

    def test_list_owid_charts_templates_returns_empty_list(self) -> None:
        assert self.service.list_owid_charts_templates() == []
