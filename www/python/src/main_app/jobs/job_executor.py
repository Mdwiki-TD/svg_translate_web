# src/main_app/jobs/job_executor.py
"""The single execution path for a job record.

Every backend ends up here:

* ``ThreadBackend``    -> a thread inside the web process (user passed in memory).
* ``ToolforgeBackend`` -> a pod running ``flask run-job-id <id>`` (user rebuilt from the DB token).
* ``flask run-job``    -> runs inline in the CLI process with the system user.

This module must NOT import ``backends`` or ``jobs_lifetime`` (see the dependency rule in PLAN.md),
otherwise the circular import between the backends and the starter comes back.
"""

from __future__ import annotations

import json
import logging
import signal
import threading
from typing import Any

from ..database.models import JobRecord
from ..database.services import JobsService
from .job_user import build_job_user
from .objects import JobData, JobsRunner
from .registry import load_job_data

logger = logging.getLogger(__name__)

EXIT_OK = 0
EXIT_CRASHED = 1
EXIT_CONFIG_ERROR = 2
EXIT_AUTH_ERROR = 3


class JobExecutor:
    """Runs an existing job record by id."""

    def __init__(self, jobs_service: JobsService | None = None) -> None:
        self.svc = jobs_service or JobsService()

    def run(
        self,
        job_id: int,
        user: dict[str, Any] | None = None,
        cancel_event: threading.Event | None = None,
        *,
        install_signal_handlers: bool = False,
    ) -> int:
        """Execute the job identified by ``job_id``.

        Args:
            job_id: Database id of the job (the record must already exist).
            user: Pre-built auth payload. When ``None`` it is rebuilt from the DB token
                of ``job.username`` (the Toolforge pod flow).
            cancel_event: Event the worker polls for cancellation. A fresh one is created if omitted.
            install_signal_handlers: Map ``SIGTERM`` to ``cancel_event.set()``. Only valid in the
                main thread, so it must stay ``False`` when called from a thread backend.

        Returns:
            Exit code: 0 = success, 1 = job crashed, 2 = config/not-found error, 3 = auth error.
        """
        job = self.svc.get_by(id=job_id)
        if job is None:
            logger.error("Job %s not found", job_id)
            return EXIT_CONFIG_ERROR

        if job.status == "cancelled":
            # Cancelled before it started.
            return EXIT_OK

        job_data = load_job_data(job.job_type)
        if not job_data or not job_data.job_class:
            self.svc.mark_failed(job, f"unknown job type {job.job_type}")
            return EXIT_CONFIG_ERROR

        if user is None:
            user = build_job_user(job.username)

        if user is None:
            self.svc.mark_failed(job, f"no token for user {job.username}")
            return EXIT_AUTH_ERROR

        if cancel_event is None:
            cancel_event = threading.Event()
        if install_signal_handlers:
            signal.signal(signal.SIGTERM, lambda *_: cancel_event.set())

        runner = self._build_runner(job, job_data, user, cancel_event)
        return self._execute(job_id, job_data, runner)

    def _execute(self, job_id: int, job_data: JobData, runner: JobsRunner) -> int:
        # The worker's own run() records status via before_run/after_run, but its constructor
        # runs outside that try block, so construction errors are handled here.
        try:
            job_data.job_class(runner).run()
        except Exception:
            logger.exception("Job %s crashed", job_id)
            job = self.svc.get_by(id=job_id)
            if job:
                self.svc.mark_failed(job, "unhandled exception")
            return EXIT_CRASHED

        # Safety net: if the worker class didn't set a final status, mark completed.
        job = self.svc.get_by(id=job_id)
        if job and job.status in ("pending", "running"):
            self.svc.mark_as_completed(job)
        return EXIT_OK

    @staticmethod
    def _build_runner(
        job: JobRecord,
        job_data: JobData,
        user: dict[str, Any],
        cancel_event: threading.Event,
    ) -> JobsRunner:
        """Single construction point for ``JobsRunner`` (previously duplicated per backend)."""
        payload: dict[str, Any] = json.loads(job.payload) if job.payload else {}
        return JobsRunner(
            job_id=job.id,
            user=user,
            cancel_event=cancel_event,
            args=payload.get("args") or {},
            form_data=payload.get("form_data"),
            job_type=job.job_type,
            job_for_admin=job_data.job_for_admin,
        )


__all__ = [
    "EXIT_AUTH_ERROR",
    "EXIT_CONFIG_ERROR",
    "EXIT_CRASHED",
    "EXIT_OK",
    "JobExecutor",
]
