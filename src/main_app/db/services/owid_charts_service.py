from __future__ import annotations

import logging
from typing import Any, Optional

from ...extensions import db
from ..models.owid_charts import OwidChartRecord
from .utils import db_guard, db_guard_rollback

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


def get_chart_by_slug(slug: str) -> Optional[OwidChartRecord]:
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
    **chart_data: dict[str, Any],
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


@db_guard_rollback
def update_chart_data(
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


# ── DELETE ───────────────────────────────────────────────


@db_guard(default_return=False)
def delete_chart(chart_id: int) -> bool:
    """Delete a chart."""
    record = db.session.query(OwidChartRecord).filter(OwidChartRecord.chart_id == chart_id).first()

    if record:
        db.session.delete(record)
        db.session.commit()
        return True
    return False


__all__ = [
    "get_chart_by_id",
    "get_chart_by_slug",
    "add_chart",
    "update_chart_data",
    "delete_chart",
    "list_charts",
    "list_published_charts",
]
