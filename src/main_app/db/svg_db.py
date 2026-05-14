"""Compatibility shim exposing legacy helpers built atop :class:`Database`."""

from __future__ import annotations

import logging
from typing import Any, Optional

from ..config import settings
from .db_class import Database
from .exceptions import InsufficientDatabaseConfigError

_db: Database | None = None

logger = logging.getLogger(__name__)


def get_db() -> Database:
    """
    Get the cached Database instance, creating and caching a new Database from settings.database_data if none exists.
    Logs an error if the database configuration is not available.

    Returns:
        Database: The cached Database instance.
    """
    global _db

    if _db is None:
        if not settings.has_db_config():
            raise InsufficientDatabaseConfigError()

        try:
            _db = Database(settings.database_data)
        except Exception as exc:  # pragma: no cover - defensive guard for startup failures
            logger.exception("Failed to initialize MySQL template store")
            raise RuntimeError("Unable to initialize template store") from exc

    return _db


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
    "execute_query",
    "fetch_query",
    "execute_query_safe",
    "fetch_query_safe",
]
