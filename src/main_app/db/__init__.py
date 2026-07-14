from __future__ import annotations

import logging
import sqlite3
from typing import Any

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

from .create_helper import create_tables, create_views
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


def receive_connect(dbapi_conn, connection_record) -> None:
    logger.debug("New connection established")


def register_events(engine) -> None:
    # Enable foreign keys for SQLite (used in tests)
    if engine.dialect.name == "sqlite":
        if not event.contains(engine, "connect", _enable_sqlite_foreign_keys):
            event.listen(engine, "connect", _enable_sqlite_foreign_keys)

    if not event.contains(engine, "connect", receive_connect):
        event.listen(engine, "connect", receive_connect)


def init_db(_db: SQLAlchemy) -> None:
    """
    Initialize database tables and views if they don't exist.

    Creates all real tables (skipping views) and creates views manually
    using the SQL stored in each view model's ``__table_args__["info"]``.
    This is idempotent-safe to call on every app startup.

    Raises:
        DatabaseInitError: If table creation fails.
    """
    from . import models  # noqa: F401 - register models on db.metadata

    register_events(_db.engine)

    # Create only real tables; skip view-backed mapped classes
    create_tables(_db)

    create_views(_db)


__all__ = [
    "init_db",
]
