"""
Utilities for managing db charts.
"""

from __future__ import annotations

import logging

from ...config import settings
from ..engine import Database
from ..exceptions import InsufficientDatabaseConfigError

logger = logging.getLogger(__name__)

_MAIN_DB: Database | None = None


def get_main_db() -> Database:
    """
    """
    global _MAIN_DB

    if _MAIN_DB is None:
        _MAIN_DB = Database(settings.database_data)

    return _MAIN_DB


def initialize_db(_db_class, db: Database | None = None):
    """
    Return the module's cached instance, initializing it on first use.
    """

    if not settings.has_db_config():
        raise InsufficientDatabaseConfigError()

    try:
        _store = _db_class(settings.database_data, db or get_main_db())
    except Exception as exc:
        logger.exception("Failed to initialize MySQL charts store")
        raise RuntimeError("Unable to initialize charts store") from exc

    return _store


__all__ = [
    "initialize_db",
]
