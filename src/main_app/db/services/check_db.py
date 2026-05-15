"""
Utilities for managing db charts.
"""

from __future__ import annotations

import logging

from ...config import settings
from ..exceptions import InsufficientDatabaseConfigError

logger = logging.getLogger(__name__)


def initialize_db(_store, _db_class):
    """
    Return the module's cached instance, initializing it on first use.
    """

    if _store is None:
        if not settings.has_db_config():
            raise InsufficientDatabaseConfigError()

        try:
            _store = _db_class(settings.database_data)
        except Exception as exc:
            logger.exception("Failed to initialize MySQL charts store")
            raise RuntimeError("Unable to initialize charts store") from exc

    return _store


__all__ = [
    "initialize_db",
]
