"""Utilities for managing OWID charts."""

from __future__ import annotations

import logging
from typing import Any, List

from ..config import settings
from ..db import has_db_config
from ..db.db_OwidCharts import OwidChartsDB
from ..shared.models import OwidChartRecord

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
        if not has_db_config():
            raise RuntimeError(
                "OWID charts administration requires database configuration; no fallback store is available."
            )

        try:
            _OWID_CHARTS_STORE = OwidChartsDB(settings.database_data)
        except Exception as exc:
            logger.exception("Failed to initialize MySQL charts store")
            raise RuntimeError("Unable to initialize charts store") from exc

    return _OWID_CHARTS_STORE


def list_charts() -> List[OwidChartRecord]:
    """Return all charts from the view."""
    store = get_owid_charts_db()
    return store.list()


def list_published_charts() -> List[OwidChartRecord]:
    """Return all published charts from the view."""
    store = get_owid_charts_db()
    return store.list_published()


def get_chart(chart_id: int) -> OwidChartRecord:
    """Fetch a single chart by ID."""
    store = get_owid_charts_db()
    return store.fetch_by_id(chart_id)


def get_chart_by_slug(slug: str) -> OwidChartRecord:
    """Fetch a single chart by slug."""
    store = get_owid_charts_db()
    return store.fetch_by_slug(slug)


def add_chart(
    slug: str,
    title: str,
    has_map_tab: bool = False,
    max_time: int | None = None,
    min_time: int | None = None,
    default_tab: str | None = None,
    is_published: bool = False,
    single_year_data: bool = False,
    len_years: int | None = None,
    has_timeline: bool = False,
) -> OwidChartRecord:
    """Add a new chart."""
    store = get_owid_charts_db()
    return store.add(
        slug=slug,
        title=title,
        has_map_tab=has_map_tab,
        max_time=max_time,
        min_time=min_time,
        default_tab=default_tab,
        is_published=is_published,
        single_year_data=single_year_data,
        len_years=len_years,
        has_timeline=has_timeline,
    )


def update_chart(
    chart_id: int,
    slug: str,
    title: str,
    has_map_tab: bool = False,
    max_time: int | None = None,
    min_time: int | None = None,
    default_tab: str | None = None,
    is_published: bool = False,
    single_year_data: bool = False,
    len_years: int | None = None,
    has_timeline: bool = False,
) -> OwidChartRecord:
    """Update an existing chart."""
    store = get_owid_charts_db()
    return store.update(
        chart_id=chart_id,
        slug=slug,
        title=title,
        has_map_tab=has_map_tab,
        max_time=max_time,
        min_time=min_time,
        default_tab=default_tab,
        is_published=is_published,
        single_year_data=single_year_data,
        len_years=len_years,
        has_timeline=has_timeline,
    )


def update_chart_data(
    chart_id: int,
    chart_data: dict[str, Any],
) -> OwidChartRecord:
    """Update chart fields if they are not None."""
    store = get_owid_charts_db()
    return store.update_chart_data(chart_id, chart_data)


def delete_chart(chart_id: int) -> OwidChartRecord:
    """Delete a chart."""
    store = get_owid_charts_db()
    return store.delete(chart_id)


__all__ = [
    "get_owid_charts_db",
    "OwidChartRecord",
    "OwidChartsDB",
    "list_charts",
    "list_published_charts",
    "get_chart",
    "get_chart_by_slug",
    "add_chart",
    "update_chart",
    "update_chart_data",
    "delete_chart",
]
