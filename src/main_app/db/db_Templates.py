from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, List

import pymysql

from ..config import DbConfig
from . import Database

logger = logging.getLogger(__name__)


@dataclass
class TemplateRecord:
    """Representation of a template."""

    id: int
    title: str
    main_file: str | None
    last_world_file: str | None
    created_at: Any | None = None
    updated_at: Any | None = None


class TemplatesDB:
    """MySQL-backed"""

    def __init__(self, database_data: DbConfig, use_bg_engine: bool = False):
        """
        Initialize the TemplatesDB with the given database configuration and ensure the templates table exists.

        Parameters:
            database_data (DbConfig): Configuration used to construct the underlying Database connection.
            use_bg_engine (bool): If True, use the background engine pool for batch jobs.
        """
        self.db = Database(database_data, use_bg_engine=use_bg_engine)
        self._ensure_table()

    def _ensure_table(self) -> None:
        """
        Ensure the `templates` table exists with the required schema.

        Creates the table if it does not already exist with these columns:
        - `id`: auto-incrementing primary key
        - `title`: unique non-null string (up to 255 chars)
        - `main_file`: nullable string (up to 255 chars)
        - `last_world_file`: nullable string (up to 255 chars)
        - `created_at`: timestamp defaulting to the current time
        - `updated_at`: timestamp defaulting to the current time and auto-updating on row changes
        """
        self.db.execute_query_safe(
            """
            CREATE TABLE IF NOT EXISTS templates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL UNIQUE,
                main_file VARCHAR(255) NULL,
                last_world_file VARCHAR(255) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )

    def _row_to_record(self, row: dict[str, Any]) -> TemplateRecord:
        return TemplateRecord(
            id=int(row["id"]),
            title=row["title"],
            main_file=row.get("main_file") or "",
            last_world_file=row.get("last_world_file") or "",
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def fetch_by_id(self, template_id: int) -> TemplateRecord:
        """Fetch a single template by its ID."""
        return self._fetch_by_id(template_id)

    def _fetch_by_id(self, template_id: int) -> TemplateRecord:
        rows = self.db.fetch_query_safe(
            """
            SELECT id, title, main_file, last_world_file, created_at, updated_at
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
            SELECT id, title, main_file, last_world_file, created_at, updated_at
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
            SELECT id, title, main_file, last_world_file, created_at, updated_at
            FROM templates
            ORDER BY id ASC
            """
        )
        return [self._row_to_record(row) for row in rows]

    def add(self, title: str, main_file: str, last_world_file: str | None = None) -> TemplateRecord:
        title = title.strip()
        main_file = main_file.strip()
        if not title:
            raise ValueError("Title is required")

        try:
            # Use execute_query to allow exception to propagate
            self.db.execute_query(
                """
                INSERT INTO templates (title, main_file, last_world_file) VALUES (%s, %s, %s)
                """,
                (title, main_file, last_world_file),
            )
        except pymysql.err.IntegrityError:
            # This assumes a UNIQUE constraint on the title column
            raise ValueError(f"Template '{title}' already exists") from None

        return self._fetch_by_title(title)

    def update_if_not_none(
        self,
        template_id: int,
        title: str | None = None,
        main_file: str | None = None,
        last_world_file: str | None = None,
    ) -> TemplateRecord:
        """
        Update the template record if the new values are not None.
        """
        _ = self._fetch_by_id(template_id)
        update_fields = []
        update_values = []

        if title is not None:
            update_fields.append("title = %s")
            update_values.append(title)
        if main_file is not None:
            update_fields.append("main_file = %s")
            update_values.append(main_file)
        if last_world_file is not None:
            update_fields.append("last_world_file = %s")
            update_values.append(last_world_file)

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
    ) -> TemplateRecord:
        _ = self._fetch_by_id(template_id)
        self.db.execute_query_safe(
            "UPDATE templates SET title = %s, main_file = %s , last_world_file = %s WHERE id = %s",
            (title, main_file, last_world_file, template_id),
        )
        return self._fetch_by_id(template_id)

    def delete(self, template_id: int) -> TemplateRecord:
        record = self._fetch_by_id(template_id)
        self.db.execute_query_safe(
            "DELETE FROM templates WHERE id = %s",
            (template_id,),
        )
        return record

    def add_or_update(self, title: str, main_file: str, last_world_file: str | None = None) -> TemplateRecord:
        title = title.strip()
        main_file = main_file.strip()

        if not title:
            logger.error("Title is required for add_or_update")

        self.db.execute_query_safe(
            """
            INSERT INTO templates (title, main_file, last_world_file) VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = COALESCE(VALUES(title), title),
                main_file = COALESCE(VALUES(main_file), main_file),
                last_world_file = COALESCE(VALUES(last_world_file), last_world_file)
            """,
            (title, main_file, last_world_file),
        )
        return self._fetch_by_title(title)


__all__ = [
    "TemplatesDB",
    "TemplateRecord",
]
