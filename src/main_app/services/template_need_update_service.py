"""Utilities for managing TemplatesNeedUpdateDB"""

from __future__ import annotations

import logging
from typing import Any, List

from ..config import DbConfig, settings
from ..db import Database
from ..db.exceptions import InsufficientDatabaseConfigError
from ..db.sql_schema_tables import sql_tables
from ..shared.models import TemplateNeedUpdateRecord

logger = logging.getLogger(__name__)

_TEMPLATE_UPDATE_STORE: TemplatesNeedUpdateDB | None = None


class TemplatesNeedUpdateDB:
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
        Ensure the `templates_need_update` table exists with the required schema.
        """
        self.db.execute_query_safe(sql_tables.templates_need_update)

    def _row_to_record(self, row: dict[str, Any]) -> TemplateNeedUpdateRecord:
        return TemplateNeedUpdateRecord(
            id=int(row["template_id"]),
            template_title=row["template_title"],
            slug=row.get("slug") or "",
            chart_year=row.get("chart_year") or "",
            template_year=row.get("template_year") or "",
        )

    def list(self) -> List[TemplateNeedUpdateRecord]:
        rows = self.db.fetch_query_safe(
            """
            SELECT
                template_id,
                template_title,
                slug,
                max_time as chart_year,
                last_world_year as template_year
            FROM templates_need_update
            ORDER BY max_time ASC
            """
        )
        return [self._row_to_record(row) for row in rows]


def get_templates_need_update_db() -> TemplatesNeedUpdateDB:
    """
    Return the module's cached TemplatesNeedUpdateDB instance, initializing it on first use.

    Returns:
        TemplatesNeedUpdateDB: The initialized and cached templates database instance.

    Raises:
        RuntimeError: If no database configuration is available.
        RuntimeError: If initializing the TemplatesNeedUpdateDB fails.
    """
    global _TEMPLATE_UPDATE_STORE

    if _TEMPLATE_UPDATE_STORE is None:
        if not settings.has_db_config():
            raise InsufficientDatabaseConfigError()

        try:
            _TEMPLATE_UPDATE_STORE = TemplatesNeedUpdateDB(settings.database_data)
        except Exception as exc:  # pragma: no cover - defensive guard for startup failures
            logger.exception("Failed to initialize MySQL template store")
            raise RuntimeError("Unable to initialize template store") from exc

    return _TEMPLATE_UPDATE_STORE


def list_templates_need_update() -> List[TemplateNeedUpdateRecord]:
    """Return all templates"""
    store = get_templates_need_update_db()
    coords = store.list()
    return coords


__all__ = [
    "get_templates_need_update_db",
    "list_templates_need_update",
]
