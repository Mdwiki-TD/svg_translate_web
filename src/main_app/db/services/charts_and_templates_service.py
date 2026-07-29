from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from ...extensions import db
from ..models import OwidChartRecord, TemplateRecord
# from .crud_service import CRUDService

logger = logging.getLogger(__name__)

@dataclass
class ChartAndTemplate:
    chart: OwidChartRecord
    template_id: int | None
    template_title: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart": self.chart.to_dict(),
            "template_id": self.template_id,
            "template_title": self.template_title,
        }

    def to_dict_joined(self) -> dict[str, Any]:
        return {
            **self.chart.to_dict(),
            "template_id": self.template_id,
            "template_title": self.template_title,
        }

class ChartsAndTemplatesService:# (CRUDService[OwidChartRecord]):
    def __init__(self) -> None:
        # super().__init__(db.session, OwidChartRecord)
        self.session = db.session

    def list_charts_with_templates_old(self) -> list[ChartAndTemplate]:
        """
        Retrieve all charts along with their associated template ID and title using a single LEFT OUTER JOIN.
        """
        query = (
            self.session.query(
                OwidChartRecord,
                TemplateRecord.id.label("template_id"),
                TemplateRecord.title.label("template_title"),
            )
            .outerjoin(TemplateRecord, TemplateRecord.slug == OwidChartRecord.slug)
            .order_by(OwidChartRecord.chart_id.asc())
        )
        result = query.all()
        return [
            ChartAndTemplate(
                chart=chart,
                template_id=template_id,
                template_title=template_title,
            )
            for chart, template_id, template_title in result
        ]

    def list_all(self) -> list[ChartAndTemplate]:
        """
        Retrieve all charts, whether they have a matching template or not (LEFT OUTER JOIN).
        If there is no matching template, template_id and template_title will be None.
        """
        query = (
            self.session.query(
                OwidChartRecord,
                TemplateRecord.id.label("template_id"),
                TemplateRecord.title.label("template_title"),
            )
            .outerjoin(TemplateRecord, TemplateRecord.slug == OwidChartRecord.slug)
            .order_by(OwidChartRecord.chart_id.asc())
        )
        result = query.all()
        return [
            ChartAndTemplate(
                chart=chart,
                template_id=template_id,
                template_title=template_title,
            )
            for chart, template_id, template_title in result
        ]

    def list_charts_with_templates(self) -> list[ChartAndTemplate]:
        """
        Retrieve charts that have a matching template only (INNER JOIN).
        """
        return [x for x in self.list_all() if x.template_id is not None]

    def list_charts_without_templates(self) -> list[OwidChartRecord]:
        """
        Retrieve charts that have no matching template.
        """
        return [x.chart for x in self.list_all() if x.template_id is None]

__all__ = [
    "ChartsAndTemplatesService",
]
