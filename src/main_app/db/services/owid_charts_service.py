"""Utilities for managing OWID charts."""

from __future__ import annotations

import logging
from typing import Any, List

from ..db_OwidCharts import OwidChartsDB
from ..models import OwidChartRecord
from .check_db import get_main_db, initialize_db

logger = logging.getLogger(__name__)

_OWID_CHARTS_STORE: OwidChartsDB | None = None


def get_owid_charts_db() -> OwidChartsDB:
    """
    Return the module's cached OwidChartsDB instance, initializing it on first use.

    Returns:
        OwidChartsDB: The initialized and cached charts database instance.

    Raises:
        RuntimeError: If no database configuration is available.
        RuntimeError: If initializing the OwidChartsDB fails.
    """
    global _OWID_CHARTS_STORE

    if _OWID_CHARTS_STORE is None:
        _OWID_CHARTS_STORE = initialize_db(OwidChartsDB, get_main_db())

    return _OWID_CHARTS_STORE


def list_charts(limit: int = 100) -> List[OwidChartRecord]:
    """
    Return all charts from the view.

    Query to match:
        SELECT * FROM owid_charts_templates oct, owid_charts oc
        WHERE oct.chart_id = oc.chart_id
        ORDER BY oc.chart_id ASC
    """
    store = get_owid_charts_db()
    return store.list()


def list_published_charts() -> List[OwidChartRecord]:
    """
    Return all published charts from the view.

    Query to match:
        SELECT * FROM owid_charts_templates oct, owid_charts oc
        WHERE oct.chart_id = oc.chart_id
        AND oc.is_published = 1
        ORDER BY oc.chart_id ASC
    """
    store = get_owid_charts_db()
    return store.list_published()


def get_chart_by_id(chart_id: int) -> OwidChartRecord:
    """
    Fetch a single chart by ID.

    Query to match:
        SELECT * FROM owid_charts_templates oct, owid_charts oc
        WHERE oct.chart_id = %s
        and oct.chart_id = oc.chart_id
    """
    store = get_owid_charts_db()
    return store.fetch_by_id(chart_id)


def get_chart_by_slug(slug: str) -> OwidChartRecord:
    """
    Fetch a single chart by slug.

    Query to match:
        SELECT * FROM owid_charts_templates oct, owid_charts oc
        WHERE oc.slug = %s
        and oct.chart_id = oc.chart_id
    """
    store = get_owid_charts_db()
    return store.fetch_by_slug(slug)


def add_chart(
    chart_data: dict[str, Any],
) -> OwidChartRecord:
    """Add a new chart."""
    chart_data.update(
        {
            "has_map_tab": 1 if chart_data.get("has_map_tab") else 0,
            "is_published": 1 if chart_data.get("is_published") else 0,
            "single_year_data": 1 if chart_data.get("single_year_data") else 0,
            "has_timeline": 1 if chart_data.get("has_timeline") else 0,
        }
    )
    store = get_owid_charts_db()
    return store.add(
        chart_data=chart_data,
    )


def update_chart_data(
    chart_id: int,
    chart_data: dict[str, Any],
) -> OwidChartRecord:
    """Update chart fields if they are not None."""
    store = get_owid_charts_db()
    return store.update_chart_data(chart_id, chart_data)


def delete_chart(chart_id: int) -> bool:
    """Delete a chart."""
    store = get_owid_charts_db()
    return store.delete(chart_id)


__all__ = [
    "get_chart_by_id",
    "get_chart_by_slug",
    "add_chart",
    "update_chart_data",
    "delete_chart",
    "list_charts",
    "list_published_charts",
]
