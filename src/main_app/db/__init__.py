from __future__ import annotations

import logging
import sqlite3
from typing import Any

from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError

from .exceptions import DatabaseInitError

logger = logging.getLogger(__name__)


def _enable_sqlite_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
    """Enable foreign key enforcement for SQLite connections."""
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()
    except sqlite3.DatabaseError as exc:
        logger.exception("Failed to enable SQLite foreign keys")
        raise DatabaseInitError("Failed to enable SQLite foreign key enforcement") from exc


def init_db(_db) -> None:
    """
    Initialize database tables and views if they don't exist.

    Creates all real tables (skipping views) and creates views manually
    using the SQL stored in each view model's ``__table_args__["info"]``.
    This is idempotent-safe to call on every app startup.

    Raises:
        DatabaseInitError: If table creation fails.
    """
    from . import models  # noqa: F401 - register models on db.metadata

    # Enable foreign keys for SQLite (used in tests)
    if _db.engine.dialect.name == "sqlite":
        if not event.contains(_db.engine, "connect", _enable_sqlite_foreign_keys):
            event.listen(_db.engine, "connect", _enable_sqlite_foreign_keys)

    # Create only real tables; skip view-backed mapped classes
    real_tables = [t for t in _db.metadata.tables.values() if not t.info.get("is_view")]
    try:
        _db.metadata.create_all(
            _db.engine,
            tables=real_tables,
            checkfirst=True,
        )
    except SQLAlchemyError as exc:
        raise DatabaseInitError(f"Failed to create tables: {exc}") from exc

    from sqlalchemy import inspect as sa_inspect

    existing_views = set(sa_inspect(_db.engine).get_view_names())
    # Create views manually (SQLite-compatible CREATE VIEW)
    with _db.engine.connect() as conn:
        for table in _db.metadata.tables.values():
            if not table.info.get("is_view"):
                continue

            if not table.info.get("create_query"):
                logger.warning("View %s has no create_query, skipping", table.name)
                continue

            if table.name in existing_views:
                continue
            try:
                with conn.begin():
                    create_sql = table.info["create_query"]
                    conn.execute(text(create_sql))
            except Exception:
                logger.exception("Failed to create view %s", table.name)


__all__ = [
    "init_db",
]
