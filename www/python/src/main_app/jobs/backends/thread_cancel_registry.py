"""In-process cancel event registry used by the thread backend only.

Cross-process cancellation of thread jobs goes through the ``.cancelled`` file (see ``JobCanceller``).
"""

from __future__ import annotations

import threading

JOBS_CANCEL_EVENTS: dict[int, threading.Event] = {}
JOBS_CANCEL_EVENTS_LOCK = threading.Lock()


def register_cancel_event(job_id: int, cancel_event: threading.Event) -> None:
    with JOBS_CANCEL_EVENTS_LOCK:
        JOBS_CANCEL_EVENTS[job_id] = cancel_event


def pop_cancel_event(job_id: int) -> threading.Event | None:
    with JOBS_CANCEL_EVENTS_LOCK:
        return JOBS_CANCEL_EVENTS.pop(job_id, None)


def get_cancel_event(job_id: int) -> threading.Event | None:
    with JOBS_CANCEL_EVENTS_LOCK:
        return JOBS_CANCEL_EVENTS.get(job_id)


__all__ = [
    "JOBS_CANCEL_EVENTS",
    "JOBS_CANCEL_EVENTS_LOCK",
    "get_cancel_event",
    "pop_cancel_event",
    "register_cancel_event",
]
