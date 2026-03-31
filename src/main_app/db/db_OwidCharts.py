from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List

import pymysql

from ..config import DbConfig
from . import Database
from .sql_schema_tables import sql_tables

logger = logging.getLogger(__name__)


@dataclass
class OwidChartRecord:
    """Representation of an OWID chart record."""

    chart_id: int
    slug: str
    title: str
    has_map_tab: bool
    max_time: int | None
    min_time: int | None
    default_tab: str | None
    is_published: bool
    single_year_data: bool
    len_years: int | None
    has_timeline: bool
    created_at: Any | None = None
    updated_at: Any | None = None
    template_id: int | None = None
    template_title: str | None = None
    template_source: str | None = None

    def __post_init__(self):
        if not self.template_source and self.slug:
            self.template_source = f"https://ourworldindata.org/grapher/{self.slug}"


class OwidChartsDB:
    """MySQL-backed storage for OWID charts."""

    def __init__(self, database_data: DbConfig):
        """
        Initialize the OwidChartsDB with the given database configuration.

        Parameters:
            database_data (DbConfig): Configuration used to construct the underlying Database connection.
        """
        self.db = Database(database_data)
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Ensure the owid_charts table exists with the required schema."""
        self.db.execute_query_safe(sql_tables.owid_charts)

    def _row_to_record(self, row: dict[str, Any]) -> OwidChartRecord:
        return OwidChartRecord(
            chart_id=int(row["chart_id"]),
            slug=row["slug"],
            title=row["title"],
            has_map_tab=bool(row.get("has_map_tab", 0)),
            max_time=row.get("max_time"),
            min_time=row.get("min_time"),
            default_tab=row.get("default_tab"),
            is_published=bool(row.get("is_published", 0)),
            single_year_data=bool(row.get("single_year_data", 0)),
            len_years=row.get("len_years"),
            has_timeline=bool(row.get("has_timeline", 0)),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
            template_id=row.get("template_id"),
            template_title=row.get("template_title"),
            template_source=row.get("template_source"),
        )

    def fetch_by_id(self, chart_id: int) -> OwidChartRecord:
        """Fetch a single chart by its ID from the view."""
        return self._fetch_by_id(chart_id)

    def _fetch_by_id(self, chart_id: int) -> OwidChartRecord:
        rows = self.db.fetch_query_safe(
            """
            SELECT * FROM owid_charts_templates oct, owid_charts oc
            WHERE oct.chart_id = %s
            and oct.chart_id = oc.chart_id
            """,
            (chart_id,),
        )
        if not rows:
            raise LookupError(f"Chart id {chart_id} was not found")
        return self._row_to_record(rows[0])

    def fetch_by_slug(self, slug: str) -> OwidChartRecord:
        """Fetch a single chart by its slug from the view."""
        rows = self.db.fetch_query_safe(
            """
            SELECT * FROM owid_charts_templates oct, owid_charts oc
            WHERE oc.slug = %s
            and oct.chart_id = oc.chart_id
            """,
            (slug,),
        )
        if not rows:
            raise LookupError(f"Chart slug {slug!r} was not found")
        return self._row_to_record(rows[0])

    def list(self) -> List[OwidChartRecord]:
        """List all charts from the view."""
        rows = self.db.fetch_query_safe(
            """
            SELECT * FROM owid_charts_templates oct, owid_charts oc
            WHERE oct.chart_id = oc.chart_id
            ORDER BY oc.chart_id ASC
            """
        )
        return [self._row_to_record(row) for row in rows]

    def list_published(self) -> List[OwidChartRecord]:
        """List all published charts from the view."""
        rows = self.db.fetch_query_safe(
            """
            SELECT * FROM owid_charts_templates oct, owid_charts oc
            WHERE oct.chart_id = oc.chart_id
            AND oc.is_published = 1
            ORDER BY oc.chart_id ASC
            """
        )
        return [self._row_to_record(row) for row in rows]

    def add(
        self,
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
        slug = slug.strip()
        title = title.strip()

        if not slug:
            raise ValueError("Slug is required")
        if not title:
            raise ValueError("Title is required")

        try:
            self.db.execute_query(
                """
                INSERT INTO owid_charts (
                    slug, title, has_map_tab, max_time, min_time,
                    default_tab, is_published, single_year_data, len_years, has_timeline
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    slug,
                    title,
                    1 if has_map_tab else 0,
                    max_time,
                    min_time,
                    default_tab,
                    1 if is_published else 0,
                    1 if single_year_data else 0,
                    len_years,
                    1 if has_timeline else 0,
                ),
            )
        except pymysql.err.IntegrityError:
            raise ValueError(f"Chart with slug '{slug}' already exists") from None

        return self.fetch_by_slug(slug)

    def update_chart_data(
        self,
        chart_id: int,
        chart_data: dict[str, Any],
    ) -> OwidChartRecord:
        """Update chart fields if they are not None."""
        _ = self._fetch_by_id(chart_id)

        update_fields = []
        update_values = []

        chart_fields = {
            "slug",
            "title",
            "has_map_tab",
            "max_time",
            "min_time",
            "default_tab",
            "is_published",
            "single_year_data",
            "len_years",
            "has_timeline",
        }

        for field in chart_fields:
            value = chart_data.get(field)
            if value is not None:
                if field in ("has_map_tab", "is_published", "single_year_data", "has_timeline"):
                    value = 1 if value else 0
                update_fields.append(f"{field} = %s")
                update_values.append(value)

        if update_fields:
            query = f"UPDATE owid_charts SET {', '.join(update_fields)} WHERE chart_id = %s"
            update_values.append(chart_id)
            self.db.execute_query_safe(query, tuple(update_values))

        return self._fetch_by_id(chart_id)

    def update(
        self,
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
        _ = self._fetch_by_id(chart_id)

        slug = slug.strip()
        title = title.strip()

        self.db.execute_query_safe(
            """
            UPDATE owid_charts
            SET slug = %s, title = %s,
                has_map_tab = %s, max_time = %s, min_time = %s,
                default_tab = %s, is_published = %s,
                single_year_data = %s, len_years = %s, has_timeline = %s
            WHERE chart_id = %s
            """,
            (
                slug,
                title,
                1 if has_map_tab else 0,
                max_time,
                min_time,
                default_tab,
                1 if is_published else 0,
                1 if single_year_data else 0,
                len_years,
                1 if has_timeline else 0,
                chart_id,
            ),
        )
        return self._fetch_by_id(chart_id)

    def delete(self, chart_id: int) -> OwidChartRecord:
        """Delete a chart."""
        record = self._fetch_by_id(chart_id)
        self.db.execute_query_safe(
            "DELETE FROM owid_charts WHERE chart_id = %s",
            (chart_id,),
        )
        return record


__all__ = [
    "OwidChartsDB",
    "OwidChartRecord",
]
