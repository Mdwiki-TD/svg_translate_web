from __future__ import annotations

import logging

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .exceptions import DatabaseInitError

logger = logging.getLogger(__name__)


def create_tables(_db: SQLAlchemy) -> None:
    real_tables = [t for t in _db.metadata.tables.values() if not t.info.get("is_view")]
    try:
        _db.metadata.create_all(
            _db.engine,
            tables=real_tables,
            checkfirst=True,
        )
    except SQLAlchemyError as exc:
        raise DatabaseInitError(f"Failed to create tables: {exc}") from exc

def create_views(_db: SQLAlchemy) -> None:
    from sqlalchemy import inspect as sa_inspect

    existing_views = set(sa_inspect(_db.engine).get_view_names())
    # Create views manually (SQLite-compatible CREATE VIEW)
    with _db.engine.connect() as conn:
        for table in _db.metadata.tables.values():
            if not table.info.get("is_view"):
                continue

            if not table.info.get("create_query"):
                logger.error("View %s has no create_query, skipping", table.name)
                continue

            create_sql = table.info["create_query"]
            if table.name in existing_views:
                if table.info.get("replace_the_view"):
                    try:
                        with conn.begin():
                            conn.execute(text(f"DROP VIEW IF EXISTS {table.name}"))
                    except Exception:
                        logger.exception("Failed to drop view %s", table.name)
                        continue
                else:
                    continue
            try:
                with conn.begin():
                    conn.execute(text(create_sql))
            except Exception:
                logger.error("Failed to create view %s", table.name)

__all__ = [
    "create_views",
    "create_tables",
]
