"""Shared cancel event registry for the thread backend.

Extracted to avoid circular imports between ``jobs_worker`` and ``backends.thread_backend``.
"""

from __future__ import annotations

import threading


class CancelEventRegistry:
    """Manages cancel events for running jobs."""

    def __init__(self) -> None:
        self._events: dict[int, threading.Event] = {}
        self._lock = threading.Lock()

    def register(self, job_id: int, cancel_event: threading.Event) -> None:
        """Register a cancel event for a job."""
        with self._lock:
            self._events[job_id] = cancel_event

    def pop(self, job_id: int) -> threading.Event | None:
        """Remove and return the cancel event for a job."""
        with self._lock:
            return self._events.pop(job_id, None)

    def get(self, job_id: int) -> threading.Event | None:
        """Get the cancel event for a job without removing it."""
        with self._lock:
            return self._events.get(job_id)


# Module-level default instance for backward compatibility
_default_registry = CancelEventRegistry()

# Legacy globals for backward compatibility
JOBS_CANCEL_EVENTS = _default_registry._events
JOBS_CANCEL_EVENTS_LOCK = _default_registry._lock


def register_cancel_event(job_id: int, cancel_event: threading.Event) -> None:
    """Legacy wrapper. Use CancelEventRegistry.register instead."""
    _default_registry.register(job_id, cancel_event)


def pop_cancel_event(job_id: int) -> threading.Event | None:
    """Legacy wrapper. Use CancelEventRegistry.pop instead."""
    return _default_registry.pop(job_id)


def get_cancel_event(job_id: int) -> threading.Event | None:
    """Legacy wrapper. Use CancelEventRegistry.get instead."""
    return _default_registry.get(job_id)


__all__ = [
    "CancelEventRegistry",
    "JOBS_CANCEL_EVENTS",
    "JOBS_CANCEL_EVENTS_LOCK",
    "register_cancel_event",
    "pop_cancel_event",
    "get_cancel_event",
]
