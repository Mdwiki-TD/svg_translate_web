from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func

from ...extensions import db
from ..models.owid_charts import OwidChartRecord
from .utils import db_guard_rollback, retry_on_db_disconnect

logger = logging.getLogger(__name__)


def list_charts(limit: int | None = None) -> list[OwidChartRecord]:
    """
    Return all charts from the view.

    Query to match:
        SELECT * FROM owid_charts_templates oct, owid_charts oc
        WHERE oct.chart_id = oc.chart_id
        ORDER BY oc.chart_id ASC
    """
    query = db.session.query(OwidChartRecord).order_by(OwidChartRecord.chart_id.asc())
    if limit is not None:
        query = query.limit(limit)

    return query.all()


def count_charts() -> int:
    """
    Return the total number of charts.
    """
    return db.session.query(func.count(OwidChartRecord.chart_id)).scalar()


def list_published_charts() -> list[OwidChartRecord]:
    """
    Return all published charts from the view.

    Query to match:
        SELECT * FROM owid_charts_templates oct, owid_charts oc
        WHERE oct.chart_id = oc.chart_id
        AND oc.is_published = 1
        ORDER BY oc.chart_id ASC
    """
    query = (
        db.session.query(OwidChartRecord)
        .filter(OwidChartRecord.is_published == 1)
        .order_by(OwidChartRecord.chart_id.asc())
    )
    records = query.all()
    return records


def get_chart_by_id(chart_id: int) -> OwidChartRecord | None:
    """
    Fetch a single chart by ID.

    Query to match:
        SELECT * FROM owid_charts_templates oct, owid_charts oc
        WHERE oct.chart_id = %s
        and oct.chart_id = oc.chart_id
    """
    records = db.session.query(OwidChartRecord).filter(OwidChartRecord.chart_id == chart_id).first()
    return records


def get_chart_by_slug(slug: str) -> OwidChartRecord | None:
    """
    Fetch a single chart by slug.

    Query to match:
        SELECT * FROM owid_charts_templates oct, owid_charts oc
        WHERE oc.slug = %s
        and oct.chart_id = oc.chart_id
    """
    return db.session.query(OwidChartRecord).filter(OwidChartRecord.slug == slug).first()


@db_guard_rollback
def add_chart(
    **chart_data: Any,
) -> OwidChartRecord:
    """
    Add a new chart.
    """
    chart_data = {
        key: value for key, value in chart_data.items() if value is not None and hasattr(OwidChartRecord, key)
    }
    chart = OwidChartRecord(**chart_data)
    db.session.add(chart)
    db.session.commit()
    db.session.refresh(chart)

    return chart


def _update_chart_data(
    chart_id: int,
    chart_data: dict[str, Any],
) -> OwidChartRecord | None:
    """
    Update chart fields if they are not None.
    """
    chart = db.session.query(OwidChartRecord).filter(OwidChartRecord.chart_id == chart_id).first()
    if not chart:
        return None

    for key, value in chart_data.items():
        if value is not None and hasattr(OwidChartRecord, key):
            setattr(chart, key, value)

    db.session.commit()
    db.session.refresh(chart)

    return chart


@db_guard_rollback
def update_chart_data(
    chart_id: int,
    chart_data: dict[str, Any],
) -> OwidChartRecord | None:
    """
    Update chart fields if they are not None.
    """
    return _update_chart_data(chart_id, chart_data)


@retry_on_db_disconnect()
def update_chart_data_with_retry(
    chart_id: int,
    chart_data: dict[str, Any],
) -> OwidChartRecord | None:
    return _update_chart_data(chart_id, chart_data)


class OwidChartsService:
    def __init__(self) -> None:
        pass

    def list_charts(self, limit: int | None = None) -> list[OwidChartRecord]:
        return list_charts(limit)

    def count_charts(self) -> int:
        return count_charts()

    def list_published_charts(self) -> list[OwidChartRecord]:
        return list_published_charts()

    def get_chart_by_id(self, chart_id: int) -> OwidChartRecord | None:
        return get_chart_by_id(chart_id)

    def get_chart_by_slug(self, slug: str) -> OwidChartRecord | None:
        return get_chart_by_slug(slug)

    def add_chart(self, **chart_data: Any) -> OwidChartRecord:
        return add_chart(**chart_data)

    def update_chart_data(
        self,
        chart_id: int,
        chart_data: dict[str, Any],
    ) -> OwidChartRecord | None:
        return update_chart_data(chart_id, chart_data)

    def update_chart_data_with_retry(
        self,
        chart_id: int,
        chart_data: dict[str, Any],
    ) -> OwidChartRecord | None:
        return update_chart_data_with_retry(chart_id, chart_data)


__all__ = [
    "OwidChartsService",
    "get_chart_by_id",
    "get_chart_by_slug",
    "add_chart",
    "list_charts",
    "count_charts",
    "list_published_charts",
    "update_chart_data",
    "update_chart_data_with_retry",
]
