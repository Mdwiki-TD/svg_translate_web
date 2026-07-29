from __future__ import annotations

import logging

from ...extensions import db
from ..models import OwidChartRecord, TemplateRecord
# from .crud_service import CRUDService

logger = logging.getLogger(__name__)


class ChartsAndTemplatesService:# (CRUDService[OwidChartRecord]):
    def __init__(self) -> None:
        # super().__init__(db.session, OwidChartRecord)
        self.session = db.session

    def list_charts_with_templates(self) -> list[tuple[OwidChartRecord, int | None, str | None]]:
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
        return query.all()

__all__ = [
    "ChartsAndTemplatesService",
]
