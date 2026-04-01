""""""

from __future__ import annotations

import logging
import threading

from ..config import settings
from ..db.task_store_pymysql import TaskStorePyMysql

TASK_STORE: TaskStorePyMysql | None = None
TASK_STORE_LOCK = threading.Lock()

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


def get_db_tasks(user=None):
    with TASK_STORE_LOCK:
        db_tasks = _task_store().list_tasks(
            username=user,
            order_by="created_at",
            descending=True,
        )

    return db_tasks


def create_new_task(
    new_task_id: str,
    title: str,
    username: str,
    form=None,
) -> None:
    with TASK_STORE_LOCK:
        _task_store().create_task(
            new_task_id,
            title,
            username=username,
            form=form,
        )


def get_store_task(task_id: str):
    with TASK_STORE_LOCK:
        task = _task_store().get_task(task_id)
    return task


def get_active_task_by_title(title: str):
    with TASK_STORE_LOCK:
        task = _task_store().get_active_task_by_title(title)
    return task


def close_task_store() -> None:
    """Close the cached :class:`TaskStorePyMysql` instance if present."""
    global TASK_STORE
    if TASK_STORE is not None:
        TASK_STORE.close()


__all__ = [
    "_task_store",
    "close_task_store",
]
