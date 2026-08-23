from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from ...extensions import db
from ..models import OwidChartRecord, TemplateRecord

logger = logging.getLogger(__name__)


@dataclass
class ChartAndTemplate:
    chart: OwidChartRecord
    template_id: int | None
    template_title: str | None

    def to_json(self) -> dict[str, Any]:
        return {
            "chart": self.chart.to_json(),
            "template_id": self.template_id,
            "template_title": self.template_title,
        }

    def to_dict_joined(self, template_filter: str = "") -> dict[str, Any]:
        data = {
            **self.chart.to_json(),
            "template_id": self.template_id,
            "template_title": self.template_title,
        }
        if not template_filter:
            return data

        if template_filter == "no_template":
            return data if self.template_id is None else {}

        if template_filter == "has_template":
            return data if self.template_id is not None else {}

        logger.error("Invalid template_filter: %s", template_filter)
        return {}


class ChartsAndTemplatesService:  # (CRUDService[OwidChartRecord]):
    def __init__(self) -> None:
        # super().__init__(db.session, OwidChartRecord)
        self.session = db.session

    def list_all(self) -> list[ChartAndTemplate]:
        """
        Retrieve all charts, whether they have a matching template or not (LEFT OUTER JOIN).
        If there is no matching template, template_id and template_title will be None.
        """
        try:
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
        except SQLAlchemyError:
            logger.exception("Error while querying charts and templates")
            return []
        except Exception as e:
            logger.error(f"Error while querying charts and templates: {e}")
            return []

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
