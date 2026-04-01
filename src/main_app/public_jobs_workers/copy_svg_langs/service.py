"""Service for copying SVG languages (translations)."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Any

from ...services import jobs_service
from .worker import copy_svg_langs_worker_entry

if TYPE_CHECKING:
    from flask import Flask

CANCEL_EVENTS: dict[str, threading.Event] = {}
CANCEL_EVENTS_LOCK = threading.Lock()

logger = logging.getLogger(__name__)


def _register_cancel_event(task_id: str, cancel_event: threading.Event) -> None:
    with CANCEL_EVENTS_LOCK:
        CANCEL_EVENTS[task_id] = cancel_event


def _pop_cancel_event(task_id: str) -> threading.Event | None:
    with CANCEL_EVENTS_LOCK:
        return CANCEL_EVENTS.pop(task_id, None)


def _runner(
    task_id: int,
    user: dict[str, Any] | None,
    cancel_event: threading.Event,
    target_func: Any,
) -> None:
    """
    """
    try:
        target_func(
            task_id,
            user,
            cancel_event=cancel_event,
        )
    finally:
        _pop_cancel_event(task_id)


def get_cancel_event(task_id: str, store: Any | None = None) -> threading.Event | None:
    """
    Retrieve the cancellation Event for a given task.

    First checks the in-memory CANCEL_EVENTS dictionary (for single-process deployments).
    If not found locally and a store is provided, falls back to checking the database
    for tasks marked as "Cancelled". This enables cross-process cancellation in
    multi-worker deployments (e.g., Gunicorn).

    Parameters:
        task_id (str): The unique identifier of the task.
        store: Optional TaskStorePyMysql instance for database lookup.

    Returns:
        threading.Event | None: The cancellation Event if the task is being cancelled,
        or None if no cancellation is in progress.

    """
    # First, try to get the cancellation event from the in-memory dictionary
    # This is fast and works for single-process deployments
    # Lock the CANCEL_EVENTS dictionary to ensure thread-safe access
    # Check if the event exists in the local dictionary
    with CANCEL_EVENTS_LOCK:
        local_event = CANCEL_EVENTS.get(task_id)
        # Return the event if found
        if local_event is not None:
            return local_event

    # Fallback: Check database for multi-process deployments
    if store is not None:
        try:
            task = store.get_task(task_id)
            if task and task.get("status") == "Cancelled":
                # Task was cancelled in another process
                event = threading.Event()
                event.set()
                return event
        except Exception:
            logger.debug("Failed to check task status in database for cancellation", exc_info=True)

    return None


def start_copy_svg_langs_job(
    title: str,
    args: Any,
    user: dict[str, Any] | None = None,
) -> int:
    """
    Start a background job to copy SVG translations.

    Args:
        title: Main file title.
        args: Job arguments.
        user: User authentication data.

    Returns:
        Job ID.
    """
    username = user.get("username") if user else None
    job = jobs_service.create_job("copy_svg_langs", username)
    task_id = job.id

    cancel_event = threading.Event()
    _register_cancel_event(task_id, cancel_event)

    thread = threading.Thread(
        target=_runner,
        args=(task_id, user, cancel_event, copy_svg_langs_worker_entry),
        kwargs={"title": title, "args": args},
        daemon=True,
    )
    thread.start()

    logger.info(f"Started copy_svg_langs job {task_id} for {title}")
    return task_id


__all__ = [
    "start_copy_svg_langs_job",
]
