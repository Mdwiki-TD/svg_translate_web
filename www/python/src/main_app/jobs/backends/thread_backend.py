"""Thread-based backend: runs jobs in threads inside the Flask process."""

from __future__ import annotations

import logging
import threading
from typing import Any

from flask import Flask, current_app

from ...database.models import JobRecord
from ..objects import JobData
from .base import JobBackend
from .thread_cancel_registry import get_cancel_event, pop_cancel_event, register_cancel_event

logger = logging.getLogger(__name__)


def _runner(
    job_id: int,
    user: dict[str, Any] | None,
    cancel_event: threading.Event,
    flask_app: Flask,
) -> None:
    """Run a job in a thread through the shared executor."""
    # Imported lazily so that importing ``backends`` never pulls in the whole workers tree.
    from ..job_executor import JobExecutor

    with flask_app.app_context():
        try:
            JobExecutor().run(job_id, user=user, cancel_event=cancel_event)
        finally:
            pop_cancel_event(job_id)


class ThreadBackend(JobBackend):
    """Runs jobs as threads inside the Flask process (dev/tests/local)."""

    def start(
        self,
        job: JobRecord,
        job_data: JobData,
        user: dict[str, Any] | None = None,
    ) -> str:
        cancel_event = threading.Event()
        register_cancel_event(job.id, cancel_event)

        flask_app = current_app._get_current_object()  # type: ignore[attr-defined]

        # Start background thread
        thread = threading.Thread(
            target=_runner,
            args=(job.id, user, cancel_event, flask_app),
            daemon=True,
        )
        try:
            thread.start()
        except Exception:
            pop_cancel_event(job.id)
            raise

        logger.info("Started thread for job %s (type=%s)", job.id, job.job_type)
        return f"thread-{job.id}"

    def cancel(self, job: JobRecord) -> bool:
        cancel_event = get_cancel_event(job.id)
        if cancel_event:
            cancel_event.set()
            logger.info("Local cancellation requested for job %s", job.id)
            return True
        return False


__all__ = [
    "ThreadBackend",
]
