from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func

from ...extensions import db
from ..models import OwidChartRecord, TemplateRecord
from .crud_service import CRUDService
from .utils import retry_on_db_disconnect

logger = logging.getLogger(__name__)


class OwidChartsService(CRUDService[OwidChartRecord]):
    def __init__(self) -> None:
        super().__init__(db.session, OwidChartRecord)

    def list_charts(self, limit: int | None = None) -> list[OwidChartRecord]:
        return self.list(
            limit=limit,
            order_by=[OwidChartRecord.chart_id.asc()],
        )

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

    def count_charts(self) -> int:
        """
        Return the total number of charts.
        """
        return self.session.query(func.count(OwidChartRecord.chart_id)).scalar()

    def list_published_charts(self) -> list[OwidChartRecord]:
        """
        Return all published charts from the view.

        Query to match:
            SELECT * FROM owid_charts_templates oct, owid_charts oc
            WHERE oct.chart_id = oc.chart_id
            AND oc.is_published = 1
            ORDER BY oc.chart_id ASC
        """
        query = (
            self.session.query(OwidChartRecord)
            .filter(OwidChartRecord.is_published == 1)
            .order_by(OwidChartRecord.chart_id.asc())
        )
        records = query.all()
        return records

    def get_chart_by_id(self, chart_id: int) -> OwidChartRecord | None:
        """
        Fetch a single chart by ID.

        Query to match:
            SELECT * FROM owid_charts_templates oct, owid_charts oc
            WHERE oct.chart_id = %s
            and oct.chart_id = oc.chart_id
        """
        records = self.session.query(OwidChartRecord).filter(OwidChartRecord.chart_id == chart_id).first()
        return records

    def get_chart_by_slug(self, slug: str) -> OwidChartRecord | None:
        """
        Fetch a single chart by slug.

        Query to match:
            SELECT * FROM owid_charts_templates oct, owid_charts oc
            WHERE oc.slug = %s
            and oct.chart_id = oc.chart_id
        """
        return self.session.query(OwidChartRecord).filter(OwidChartRecord.slug == slug).first()

    def add_chart(self, **chart_data: Any) -> OwidChartRecord | None:
        """
        Add a new chart.
        """
        chart_data = {
            key: value for key, value in chart_data.items() if value is not None and hasattr(OwidChartRecord, key)
        }
        try:
            chart = OwidChartRecord(**chart_data)
            self.session.add(chart)
            self.session.commit()
            self.session.refresh(chart)
            return chart
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding chart: {e}")
            return None

    def update_chart_data(
        self,
        chart_id: int,
        chart_data: dict[str, Any],
    ) -> OwidChartRecord | None:
        """
        Update chart fields if they are not None.
        """
        try:
            return self._update_chart_data(chart_id, chart_data)
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating chart data: {e}")
            return None

    def update_chart_data_with_retry(
        self,
        chart_id: int,
        chart_data: dict[str, Any],
    ) -> OwidChartRecord | None:

        @retry_on_db_disconnect
        def with_retry() -> OwidChartRecord | None:
            return self._update_chart_data(chart_id, chart_data)

        return with_retry()

    def _update_chart_data(
        self,
        chart_id: int,
        chart_data: dict[str, Any],
    ) -> OwidChartRecord | None:
        """
        Update chart fields if they are not None.
        """
        chart = self.session.query(OwidChartRecord).filter(OwidChartRecord.chart_id == chart_id).first()
        if not chart:
            return None

        for key, value in chart_data.items():
            if value is not None and hasattr(OwidChartRecord, key):
                setattr(chart, key, value)

        self.session.commit()
        self.session.refresh(chart)

        return chart


__all__ = [
    "OwidChartsService",
]
