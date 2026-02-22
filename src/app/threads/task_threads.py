"""Main Flask views for the SVG Translate web application."""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict

from ..config import settings
from .web_run_task import run_task

CANCEL_EVENTS: Dict[str, threading.Event] = {}
CANCEL_EVENTS_LOCK = threading.Lock()
# The use of a global dictionary CANCEL_EVENTS with a threading.Lock ties the cancellation mechanism to a single-process, multi-threaded server model. This approach will not work correctly in a multi-process environment (e.g., when using Gunicorn with multiple worker processes), as each process would have its own independent copy of CANCEL_EVENTS. For a more scalable and robust solution, consider using a shared external store like Redis or a database to manage cancellation state across processes.

logger = logging.getLogger("svg_translate")


def _register_cancel_event(task_id: str, cancel_event: threading.Event) -> None:
    with CANCEL_EVENTS_LOCK:
        CANCEL_EVENTS[task_id] = cancel_event


def _pop_cancel_event(task_id: str) -> threading.Event | None:
    with CANCEL_EVENTS_LOCK:
        return CANCEL_EVENTS.pop(task_id, None)


def get_cancel_event(task_id: str) -> threading.Event | None:
    with CANCEL_EVENTS_LOCK:
        return CANCEL_EVENTS.get(task_id)


def launch_task_thread(
    task_id: str,
    title: str,
    args: Any,
    user_payload: Dict[str, Any],
) -> None:
    """
    Start and manage a background thread that runs a task and exposes a cancellation event for that task.
    
    Registers a cancellation Event for the given task_id in the module-level cancel registry, launches a daemon thread named "task-runner-<first8_of_task_id>" to execute the task, and ensures the cancellation Event is removed from the registry once the task completes.
    
    Parameters:
        task_id (str): Unique identifier for the task; used to register and later remove the task's cancellation event.
        title (str): Human-readable title for the task.
        args (Any): Task-specific arguments passed through to the task runner.
        user_payload (Dict[str, Any]): Additional user-provided metadata passed to the task.
    
    """
    cancel_event = threading.Event()
    _register_cancel_event(task_id, cancel_event)

    def _runner() -> None:
        """
        Execute the task runner and ensure its cancellation event is removed when finished.
        
        Calls run_task with the captured settings.database_data, task_id, title, args, user_payload, and cancel_event; after run_task returns or raises, removes the task's cancel event from the global registry to avoid leaking state.
        """
        try:
            run_task(
                settings.database_data,
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
        name=f"task-runner-{task_id[:8]}",
        daemon=True,
    )
    t.start()


__all__ = [
    "get_cancel_event",
    "launch_task_thread",
]