from __future__ import annotations

import logging
from typing import List, Optional

from ..sqlalchemy_models.owid_charts import OwidChartRecord
from ..engine import get_session

logger = logging.getLogger(__name__)


def get_chart_by_slug(slug: str) -> Optional[OwidChartRecord]:
    """Fetch a chart by slug."""
    with get_session() as session:
        return session.query(OwidChartRecord).filter(OwidChartRecord.slug == slug).first()


def upsert_chart(chart_data: dict) -> OwidChartRecord:
    """Insert or update a chart record."""
    slug = chart_data.get("slug")
    with get_session() as session:
        chart = session.query(OwidChartRecord).filter(OwidChartRecord.slug == slug).first()
        if chart:
            for key, value in chart_data.items():
                setattr(chart, key, value)
        else:
            chart = OwidChartRecord(**chart_data)
            session.add(chart)
        session.commit()
        session.refresh(chart)
        return chart


def list_charts(limit: int = 100) -> List[OwidChartRecord]:
    """List charts."""
    with get_session() as session:
        return session.query(OwidChartRecord).limit(limit).all()


__all__ = [
    "get_chart_by_slug",
    "upsert_chart",
    "list_charts",
]
