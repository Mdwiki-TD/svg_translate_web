"""Compatibility shim exposing legacy helpers built atop :class:`Database`."""

from __future__ import annotations

import logging
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


__all__ = [
    "get_db",
]
