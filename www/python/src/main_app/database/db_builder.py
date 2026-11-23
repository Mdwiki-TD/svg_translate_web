from __future__ import annotations

import logging
import sqlite3
from typing import Any

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

from .create_helper import create_tables, create_views
from .exceptions import DatabaseInitError

logger = logging.getLogger(__name__)


class DatabaseBuilder:
    @staticmethod
    def enable_sqlite_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
        """Enable foreign key enforcement for SQLite connections."""
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()
        except sqlite3.DatabaseError as exc:
            logger.exception("Failed to enable SQLite foreign keys")
            raise DatabaseInitError("Failed to enable SQLite foreign key enforcement") from exc

    @staticmethod
    def receive_connect(dbapi_conn, connection_record) -> None:
        logger.debug("New connection established")

    @classmethod
    def register_events(cls, engine) -> None:
        # Enable foreign keys for SQLite (used in tests)
        if engine.dialect.name == "sqlite":
            if not event.contains(engine, "connect", cls.enable_sqlite_foreign_keys):
                event.listen(engine, "connect", cls.enable_sqlite_foreign_keys)

        # if not event.contains(engine, "connect", cls.receive_connect):
        #     event.listen(engine, "connect", cls.receive_connect)

    @staticmethod
    def cleanup_stale_jobs() -> None:
        # Clean up stale thread jobs left over from a previous run
        from .services import JobsService

        try:
            JobsService().cleanup_stale_jobs_on_startup()
        except Exception:
            logger.exception("Failed to clean up stale jobs on startup")

    @classmethod
    def init_db(cls, _db: SQLAlchemy, app: Flask) -> None:
        """
        Initialize database tables and views if they don't exist.

        Creates all real tables (skipping views) and creates views manually
        using the SQL stored in each view model's ``__table_args__["info"]``.
        This is idempotent-safe to call on every app startup.

        Raises:
            DatabaseInitError: If table creation fails.
        """
        # from . import models

        cls.register_events(_db.engine)

        # Create only real tables; skip view-backed mapped classes
        create_tables(_db)

        create_views(_db)

        # Clean up stale thread jobs left over from a previous run
        cls.cleanup_stale_jobs()

    @classmethod
    def build(cls, _db: SQLAlchemy, app: Flask) -> bool:
        try:
            with app.app_context():
                # Create database tables and views if they don't exist
                cls.init_db(_db, app)
            return True
        except DatabaseInitError as exc:
            logger.error("%s", exc)
        except Exception as e:
            logger.error("Failed to create tables: %s", e)

        return False


__all__ = [
    "DatabaseBuilder",
]
