from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from typing import Any, List

import pymysql

from ..config import DbConfig
from . import Database
from .sql_schema_tables import sql_tables

logger = logging.getLogger(__name__)


def match_last_world_year(last_world_file) -> int | None:
    """
    death-rate-by-source-from-indoor-air-pollution,World,2021.svg
    """
    # match year
    y_match = re.match(r"^.*?,\s*(\d{4})\.svg$", last_world_file)
    if y_match:
        return int(y_match.group(1))

    return None


def _strip_file_prefix(value: str | None) -> str | None:
    """Remove 'File:' prefix from a filename if present.

    Args:
        value: The filename string that may have a 'File:' prefix.

    Returns:
        The filename without the 'File:' prefix, or None if input is None.
    """
    if value is None:
        return None
    stripped = value.strip()
    if stripped.lower().startswith("file:"):
        return stripped[5:]  # Remove 'File:' prefix
    return stripped


@dataclass
class TemplateRecord:
    """Representation of a template."""

    id: int
    title: str
    main_file: str | None
    last_world_file: str | None
    last_world_year: str | None = None
    source: str | None = None
    slug: str | None = None
    created_at: Any | None = None
    updated_at: Any | None = None

    def __post_init__(self):
        if not self.slug and self.source and "/grapher/" in self.source:
            slug = self.source.split("/grapher/", maxsplit=1)[1].split("?")[0]
            self.slug = slug or None

            if not self.last_world_year and self.last_world_file:
                self.last_world_year = match_last_world_year(self.last_world_file)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "main_file": self.main_file,
            "last_world_file": self.last_world_file,
            "last_world_year": self.last_world_year,
            "source": self.source,
            "slug": self.slug,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class TemplatesDB:
    """MySQL-backed"""

    def __init__(self, database_data: DbConfig):
        """
        Initialize the TemplatesDB with the given database configuration and ensure the templates table exists.

        Parameters:
            database_data (DbConfig): Configuration used to construct the underlying Database connection.
        """
        self.db = Database(database_data)
        self._ensure_table()

    def _ensure_table(self) -> None:
        """
        Ensure the `templates` table exists with the required schema.

        Creates the table if it does not already exist with these columns:
        - `id`: auto-incrementing primary key
        - `title`: unique non-null string (up to 255 chars)
        - `main_file`: nullable string (up to 255 chars)
        - `last_world_file`: nullable string (up to 255 chars)
        - `source`: non-null string (up to 255 chars), defaults to empty string
        - `slug`: non-null string (up to 255 chars), defaults to empty string
        - `created_at`: timestamp defaulting to the current time
        - `updated_at`: timestamp defaulting to the current time and auto-updating on row changes
        """
        self.db.execute_query_safe(sql_tables.templates)

    def _row_to_record(self, row: dict[str, Any]) -> TemplateRecord:
        return TemplateRecord(
            id=int(row["id"]),
            title=row["title"],
            main_file=row.get("main_file") or "",
            last_world_file=row.get("last_world_file") or "",
            last_world_year=row.get("last_world_year") or "",
            source=row.get("source") or "",
            slug=row.get("slug") or "",
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def fetch_by_id(self, template_id: int) -> TemplateRecord:
        """Fetch a single template by its ID."""
        return self._fetch_by_id(template_id)

    def _fetch_by_id(self, template_id: int) -> TemplateRecord:
        rows = self.db.fetch_query_safe(
            """
            SELECT id, title, main_file, last_world_file, created_at, updated_at, source, slug
            FROM templates
            WHERE id = %s
            """,
            (template_id,),
        )
        if not rows:
            raise LookupError(f"Template id {template_id} was not found")
        return self._row_to_record(rows[0])

    def _fetch_by_title(self, title: str) -> TemplateRecord:
        rows = self.db.fetch_query_safe(
            """
            SELECT id, title, main_file, last_world_file, created_at, updated_at, source, slug
            FROM templates
            WHERE title = %s
            """,
            (title,),
        )
        if not rows:
            raise LookupError(f"Template {title!r} was not found")
        return self._row_to_record(rows[0])

    def list(self) -> List[TemplateRecord]:
        rows = self.db.fetch_query_safe(
            """
            SELECT id, title, main_file, last_world_file, created_at, updated_at, source, slug
            FROM templates
            ORDER BY id ASC
            """
        )
        return [self._row_to_record(row) for row in rows]

    def add_data(
        self,
        template_data: dict,
    ) -> TemplateRecord:

        add_fields = []
        add_values = []
        add_data = {}

        template_fields = {
            "title",
            "main_file",
            "last_world_file",
            "last_world_year",
            "source",
            "slug",
        }
        strip_fields = {
            "main_file",
            "last_world_file",
        }
        for field in template_fields:
            value = template_data.get(field)
            if value is None:
                continue

            if field in strip_fields:
                value = _strip_file_prefix(value)

            add_data[field] = value
            add_fields.append(field)
            add_values.append(value)

        if not add_data.get("title"):
            raise ValueError("Title is required")

        title = add_data["title"]

        try:
            # Use execute_query to allow exception to propagate
            self.db.execute_query(
                f"""
                INSERT INTO templates ({', '.join(add_fields)})
                VALUES ({', '.join(["%s" for x in add_fields])})
                """,
                tuple(add_values),
            )
        except pymysql.err.IntegrityError:
            # This assumes a UNIQUE constraint on the title column
            raise ValueError(f"Template '{title}' already exists") from None

        return self._fetch_by_title(title)

    def add(
        self,
        title: str,
        main_file: str,
        last_world_file: str | None = None,
        source: str | None = None,
        slug: str | None = None,
    ) -> TemplateRecord:
        title = title.strip()
        main_file = _strip_file_prefix(main_file) or ""
        last_world_file = _strip_file_prefix(last_world_file)
        if not title:
            raise ValueError("Title is required")

        add_fields = []
        add_values = []

        template_fields = {
            "title": title,
            "main_file": main_file,
            "last_world_file": last_world_file,
            "source": source,
            "slug": slug,
        }
        for field, value in template_fields.items():
            if value is not None:
                # update_fields.append(f"{field} = %s")
                add_fields.append(field)
                add_values.append(value)

        try:
            # Use execute_query to allow exception to propagate
            self.db.execute_query(
                f"""
                INSERT INTO templates ({', '.join(add_fields)})
                VALUES ({', '.join(["%s" for x in add_fields])})
                """,
                tuple(add_values),
            )
        except pymysql.err.IntegrityError:
            # This assumes a UNIQUE constraint on the title column
            raise ValueError(f"Template '{title}' already exists") from None

        return self._fetch_by_title(title)

    def update_template_data(
        self,
        template_id: int,
        template_data: dict[str, str],
    ) -> TemplateRecord:
        """
        Update the template record if the new values are not None.
        """
        _ = self._fetch_by_id(template_id)
        update_fields = []
        update_values = []

        template_fields_keys = {
            "title",
            "main_file",
            "last_world_file",
            "last_world_year",
            "source",
            "slug",
        }
        for field in template_fields_keys:
            value = template_data.get(field)
            if value is not None:
                update_fields.append(f"{field} = %s")
                update_values.append(value)

        if update_fields:
            query = f"UPDATE templates SET {', '.join(update_fields)} WHERE id = %s"
            update_values.append(template_id)
            self.db.execute_query_safe(query, tuple(update_values))

        return self._fetch_by_id(template_id)

    def update_if_not_none(
        self,
        template_id: int,
        title: str | None = None,
        main_file: str | None = None,
        last_world_file: str | None = None,
        source: str | None = None,
        slug: str | None = None,
    ) -> TemplateRecord:
        """
        Update the template record if the new values are not None.
        """
        _ = self._fetch_by_id(template_id)
        update_fields = []
        update_values = []

        template_fields = {
            "title": title,
            "main_file": _strip_file_prefix(main_file),
            "last_world_file": _strip_file_prefix(last_world_file),
            "source": source,
            "slug": slug,
        }
        for field, value in template_fields.items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                update_values.append(value)

        if update_fields:
            query = f"UPDATE templates SET {', '.join(update_fields)} WHERE id = %s"
            update_values.append(template_id)
            self.db.execute_query_safe(query, tuple(update_values))

        return self._fetch_by_id(template_id)

    def update(
        self,
        template_id: int,
        title: str,
        main_file: str,
        last_world_file: str | None = None,
        source: str | None = None,
        slug: str | None = None,
    ) -> TemplateRecord:
        _ = self._fetch_by_id(template_id)
        main_file = _strip_file_prefix(main_file) or ""
        last_world_file = _strip_file_prefix(last_world_file)
        self.db.execute_query_safe(
            """
            UPDATE templates
                SET title = %s, main_file = %s, last_world_file = %s, source = %s, slug = %s
            WHERE
                id = %s
            """,
            (title, main_file, last_world_file, source, slug, template_id),
        )
        return self._fetch_by_id(template_id)

    def delete(self, template_id: int) -> TemplateRecord:
        record = self._fetch_by_id(template_id)
        self.db.execute_query_safe(
            "DELETE FROM templates WHERE id = %s",
            (template_id,),
        )
        return record


__all__ = [
    "TemplatesDB",
    "TemplateRecord",
]
