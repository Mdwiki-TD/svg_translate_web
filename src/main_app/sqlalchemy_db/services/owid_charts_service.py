from __future__ import annotations

import logging
from typing import Any, List, Optional

from sqlalchemy.orm import joinedload

from ...extensions import db
from ..models.owid_charts import OwidChartRecord

# from ..models.views import OwidChartTemplateRecord

logger = logging.getLogger(__name__)


def list_charts(limit: int | None = None) -> List[OwidChartRecord]:
    """
    Return all charts from the view.

    Query to match:
        SELECT * FROM owid_charts_templates oct, owid_charts oc
        WHERE oct.chart_id = oc.chart_id
        ORDER BY oc.chart_id ASC
    """
    query = (
        db.session.query(OwidChartRecord)
        .options(joinedload(OwidChartRecord._template_info))
        .order_by(OwidChartRecord.chart_id.asc())
    )
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def list_published_charts() -> List[OwidChartRecord]:
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
        .options(joinedload(OwidChartRecord._template_info))
        .order_by(OwidChartRecord.chart_id.asc())
    )
    records = query.all()
    return records


def get_chart_by_id(chart_id: int) -> OwidChartRecord:
    """
    Fetch a single chart by ID.

    Query to match:
        SELECT * FROM owid_charts_templates oct, owid_charts oc
        WHERE oct.chart_id = %s
        and oct.chart_id = oc.chart_id
    """
    return (
        db.session.query(OwidChartRecord)
        .filter(OwidChartRecord.chart_id == chart_id)
        .options(joinedload(OwidChartRecord._template_info))
        .first()
    )


def get_chart_by_slug(slug: str) -> Optional[OwidChartRecord]:
    """
    Fetch a single chart by slug.

    Query to match:
        SELECT * FROM owid_charts_templates oct, owid_charts oc
        WHERE oc.slug = %s
        and oct.chart_id = oc.chart_id
    """
    return (
        db.session.query(OwidChartRecord)
        .filter(OwidChartRecord.slug == slug)
        .options(joinedload(OwidChartRecord._template_info))
        .first()
    )


def add_chart(
    chart_data: dict[str, Any],
) -> OwidChartRecord:
    """
    Add a new chart.
    """
    chart_data.update(
        {
            "has_map_tab": 1 if chart_data.get("has_map_tab") else 0,
            "is_published": 1 if chart_data.get("is_published") else 0,
            "single_year_data": 1 if chart_data.get("single_year_data") else 0,
            "has_timeline": 1 if chart_data.get("has_timeline") else 0,
        }
    )
    chart = OwidChartRecord(**chart_data)
    db.session.add(chart)
    db.session.commit()
    db.session.refresh(chart)
    return chart


def update_chart_data(
    chart_id: int,
    chart_data: dict[str, Any],
) -> OwidChartRecord:
    """
    Update chart fields if they are not None.
    """
    chart = db.session.query(OwidChartRecord).filter(OwidChartRecord.chart_id == chart_id).first()
    if chart:
        for key, value in chart_data.items():
            if value is not None:
                setattr(chart, key, value)
    db.session.commit()
    db.session.refresh(chart)
    return chart


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
