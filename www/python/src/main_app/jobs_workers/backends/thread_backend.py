"""Thread-based backend: runs jobs in threads inside the Flask process."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

from flask import Flask, current_app

from ...database.models import JobRecord
from ..cancel_registry import get_cancel_event
from ..cancel_registry import pop_cancel_event
from ..cancel_registry import register_cancel_event
from ..objects import JobData, JobsRunner
from .base import JobBackend

logger = logging.getLogger(__name__)


def _runner(
    runner_data: JobsRunner,
    target_class: Callable[[JobsRunner]],
    flask_app: Flask,
) -> None:
    """Run a job in a thread with proper exception handling."""
    with flask_app.app_context():
        try:
            worker = target_class(runner_data)
            worker.run()
        finally:
            pop_cancel_event(runner_data.job_id)


class ThreadBackend(JobBackend):
    """Runs jobs as threads inside the Flask process (dev/tests/local)."""

    def start(
        self,
        job: JobRecord,
        job_data: JobData,
        payload: dict[str, Any],
    ) -> str:
        cancel_event = threading.Event()
        register_cancel_event(job.id, cancel_event)

        runner_data = JobsRunner(
            job_id=job.id,
            user=payload["user"],
            cancel_event=cancel_event,
            args=payload["args"],
            form_data=payload["form_data"],
        )

        flask_app = current_app._get_current_object()  # type: ignore[attr-defined]

        # Start background thread
        thread = threading.Thread(
            target=_runner,
            args=(runner_data, job_data.job_class, flask_app),
            daemon=True,
        )
        thread.start()

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
