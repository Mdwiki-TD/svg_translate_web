from __future__ import annotations

import logging

from flask import Flask
from sqlalchemy import text

logger = logging.getLogger(__name__)


def init_db(app: Flask, _db) -> None:
    """Initialize database tables and views if they don't exist.

    Creates all real tables (skipping views) and creates views manually
    using the SQL stored in each view model's ``__table_args__["info"]``.
    This is idempotent-safe to call on every app startup.

    Args:
        app: Flask application instance with ``db.init_app()`` already called.
    """
    from . import models  # noqa: F401 - register models on db.metadata

    with app.app_context():
        # Create only real tables; skip view-backed mapped classes
        real_tables = [t for t in _db.metadata.tables.values() if not t.info.get("is_view")]
        _db.metadata.create_all(_db.engine, tables=real_tables, checkfirst=True)

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
                    create_sql = table.info["create_query"]
                    conn.execute(text(create_sql))
                    conn.commit()
                except Exception:
                    conn.rollback()
                    logger.exception("Failed to create view %s", table.name)
