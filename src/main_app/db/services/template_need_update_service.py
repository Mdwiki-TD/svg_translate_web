"""Utilities for managing TemplatesNeedUpdateDB"""

from __future__ import annotations

import logging
from typing import Any, List

from ...config import DbConfig
from .. import Database
from ..models import TemplateNeedUpdateRecord
from ..sql_schema_tables import sql_tables
from .check_db import initialize_db

logger = logging.getLogger(__name__)

_TEMPLATE_UPDATE_STORE: TemplatesNeedUpdateDB | None = None


class TemplatesNeedUpdateDB:
    """MySQL-backed"""

    def __init__(self, database_data: DbConfig | None = None, db: Database | None = None):
        """
        Initialize the TemplatesDB with the given database configuration and ensure the templates table exists.

        Parameters:
            database_data (DbConfig): Configuration used to construct the underlying Database connection.
        """
        self.db = db or Database(database_data)

    def _row_to_record(self, row: dict[str, Any]) -> TemplateNeedUpdateRecord:
        return TemplateNeedUpdateRecord(
            template_id=int(row["template_id"]),
            template_title=row["template_title"],
            slug=row.get("slug") or "",
            max_time=row.get("max_time") or "",
            last_world_year=row.get("last_world_year") or "",
        )

    def list(self) -> List[TemplateNeedUpdateRecord]:
        rows = self.db.fetch_query_safe(
            """
            SELECT
                template_id,
                template_title,
                slug,
                max_time as max_time,
                last_world_year as last_world_year
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
        _TEMPLATE_UPDATE_STORE = initialize_db(TemplatesNeedUpdateDB)

    return _TEMPLATE_UPDATE_STORE


def list_templates_need_update() -> List[TemplateNeedUpdateRecord]:
    """Return all templates"""
    store = get_templates_need_update_db()
    coords = store.list()
    return coords


__all__ = [
    "list_templates_need_update",
]
