""""""

from __future__ import annotations

import logging

from ..config import settings
from ..db.task_store_pymysql import TaskStorePyMysql

TASK_STORE: TaskStorePyMysql | None = None
logger = logging.getLogger(__name__)


def _task_store() -> TaskStorePyMysql:
    """
    Get the singleton TaskStorePyMysql instance, creating and caching it on first use.

    The store is initialized with settings.database_data and reused for subsequent calls.

    Returns:
        TaskStorePyMysql: The cached TaskStorePyMysql instance.
    """
    global TASK_STORE
    if TASK_STORE is None:
        TASK_STORE = TaskStorePyMysql(settings.database_data)
    return TASK_STORE


def close_task_store() -> None:
    """Close the cached :class:`TaskStorePyMysql` instance if present."""
    global TASK_STORE
    if TASK_STORE is not None:
        TASK_STORE.close()


__all__ = [
    "_task_store",
    "close_task_store",
]
