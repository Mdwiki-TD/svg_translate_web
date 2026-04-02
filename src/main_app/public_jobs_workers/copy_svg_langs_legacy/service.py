"""Main Flask views for the SVG Translate web application."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING, Any, Dict

from flask import current_app
from .worker import copy_svg_langs_worker_entry

if TYPE_CHECKING:
    from flask import Flask

CANCEL_EVENTS: Dict[str, threading.Event] = {}
CANCEL_EVENTS_LOCK = threading.Lock()

logger = logging.getLogger(__name__)


def _register_cancel_event(task_id: str, cancel_event: threading.Event) -> None:
    with CANCEL_EVENTS_LOCK:
        CANCEL_EVENTS[task_id] = cancel_event


def _pop_cancel_event(task_id: str) -> threading.Event | None:
    with CANCEL_EVENTS_LOCK:
        return CANCEL_EVENTS.pop(task_id, None)


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
    task_id: str,
    title: str,
    args: Any,
    user_payload: Dict[str, Any],
) -> None:
    """
    Start and manage a background thread that runs a task and exposes a cancellation event for that task.

    Registers a cancellation Event for the given task_id in the module-level cancel registry, launches a daemon thread named "task-runner-<first8_of_task_id>" to execute the task, and ensures the cancellation Event is removed from the registry once the task completes.

    This function captures the current Flask application context and pushes it within the background thread, allowing access to Flask globals (current_app, g, etc.) during task execution.

    Parameters:
        task_id (str): Unique identifier for the task; used to register and later remove the task's cancellation event.
        title (str): Human-readable title for the task.
        args (Any): Task-specific arguments passed through to the task runner.
        user_payload (Dict[str, Any]): Additional user-provided metadata passed to the task.

    """
    cancel_event = threading.Event()
    _register_cancel_event(task_id, cancel_event)

    # Capture the app context for use in the background thread
    # Unwrap the proxy to get the real app object
    try:
        app = current_app._get_current_object()
    except RuntimeError:
        # No active app context (shouldn't happen in normal operation)
        logger.error("No Flask application context available for task %s", task_id)
        raise

    def _runner(app: Flask) -> None:
        """
        Execute the task runner within the Flask app context.

        Calls copy_svg_langs_worker_entry with the captured settings.database_data, task_id, title, args, user_payload, and cancel_event; after copy_svg_langs_worker_entry returns or raises, removes the task's cancel event from the global registry to avoid leaking state.
        """
        with app.app_context():
            try:
                copy_svg_langs_worker_entry(
                    task_id,
                    title,
                    args,
                    user_payload,
                    cancel_event=cancel_event,
                )
            finally:
                _pop_cancel_event(task_id)

    t = threading.Thread(
        target=_runner,
        args=(app,),  # Pass app to the thread
        name=f"task-runner-{task_id[:8]}",
        daemon=True,
    )
    t.start()


__all__ = [
    "get_cancel_event",
    "start_copy_svg_langs_job",
]
