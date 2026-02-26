"""Compatibility shim exposing legacy helpers built atop :class:`Database`."""

from __future__ import annotations

import logging
from typing import Any, Optional

from ..config import settings
from .db_class import Database
from .db_sqlalchemy import DatabaseSQLAlchemy
from .engine_factory import USE_SQLALCHEMY_POOLING

_db: Database | DatabaseSQLAlchemy | None = None

logger = logging.getLogger(__name__)


def has_db_config() -> bool:
    """
    Return whether the application has database connection settings configured.

    Returns:
        `True` if `db_host` or `db_user` is set in `settings.database_data`, `False` otherwise.
    """
    db_settings = settings.database_data or {}
    return bool(db_settings.db_host or db_settings.db_user)


def get_db(use_background_engine: bool = False) -> Database | DatabaseSQLAlchemy:
    """
    Get the cached Database instance, creating and caching a new Database from settings.database_data if none exists.

    Args:
        use_background_engine: Use background-optimized engine for batch processing

    Returns:
        The cached Database instance.
    """
    global _db

    if not has_db_config():
        logger.error("MySQL configuration is not available for the user token store.")

    if _db is None:
        if USE_SQLALCHEMY_POOLING:
            _db = DatabaseSQLAlchemy(
                settings.database_data,
                use_background_engine=use_background_engine,
            )
            logger.debug("event=get_db engine=sqlalchemy")
        else:
            _db = Database(settings.database_data)
            logger.debug("event=get_db engine=pymysql")

    return _db


def close_cached_db() -> None:
    """Close the cached Database instance if it has been initialized."""
    global _db
    if _db is not None:
        _db.close()
        _db = None
        logger.debug("event=close_cached_db")


def execute_query(sql_query: str, params: Optional[Any] = None):
    """Proxy :meth:`Database.execute_query` for backwards compatibility."""
    with get_db() as db:
        return db.execute_query(sql_query, params)


def fetch_query(sql_query: str, params: Optional[Any] = None):
    """Proxy :meth:`Database.fetch_query` for backwards compatibility."""
    with get_db() as db:
        return db.fetch_query(sql_query, params)


def execute_query_safe(sql_query: str, params: Optional[Any] = None):
    """Proxy :meth:`Database.execute_query_safe` for backwards compatibility."""
    with get_db() as db:
        return db.execute_query_safe(sql_query, params)


def fetch_query_safe(sql_query: str, params: Optional[Any] = None):
    """Proxy :meth:`Database.fetch_query_safe` for backwards compatibility."""
    with get_db() as db:
        return db.fetch_query_safe(sql_query, params)


__all__ = [
    "get_db",
    "has_db_config",
    "close_cached_db",
    "execute_query",
    "fetch_query",
    "execute_query_safe",
    "fetch_query_safe",
]
