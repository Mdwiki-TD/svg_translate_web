# src/main_app/jobs/jobs_lifetime/jobs_starter.py
"""Starting background jobs.

Two entry points, one creation path and one execution path:

* ``start`` / ``submit_form``: web/front-end. Create the record, then hand it to a backend
  (thread or Toolforge pod) which runs it independently through ``JobExecutor``.
* ``run_now``: background/CLI jobs (e.g. ``collect_templates_data``). Create the record and run it
  inline in the current process, with no backend and no user token.
"""

from __future__ import annotations

import logging
from typing import Any

from ...database.services import JobsService
from ..backends import BackendRegistry
from ..job_executor import JobExecutor
from ..job_user import system_user
from .job_creator import JobCreator

logger = logging.getLogger(__name__)

# Stored in the ``backend`` column of jobs that are executed inline by the CLI.
INLINE_BACKEND_NAME = "cli"


class JobStarter:
    """Creates jobs and either dispatches them to a backend or runs them inline."""

    def __init__(
        self,
        jobs_service: JobsService | None = None,
        creator: JobCreator | None = None,
        executor: JobExecutor | None = None,
        backend_registry: BackendRegistry | None = None,
    ) -> None:
        """Initialize with optional dependencies."""
        self.jobs_service = jobs_service or JobsService()
        self.creator = creator or JobCreator(self.jobs_service)
        self.executor = executor or JobExecutor(self.jobs_service)
        self.backend_registry = backend_registry or BackendRegistry()

    def _dispatch(
        self,
        auth_payload: dict[str, Any] | None,
        job_type: str,
        args: dict[str, Any] | None,
        form_data: dict[str, Any] | None,
    ) -> int:
        username = auth_payload.get("username") if auth_payload else None
        if not username:
            raise ValueError("User authentication data is required")

        backend_name = self.backend_registry.get_backend_name(job_type)
        created = self.creator.create(
            username=username,
            job_type=job_type,
            backend_name=backend_name,
            args=args,
            form_data=form_data,
        )

        # The auth payload is handed over in memory only; it is never written to the DB.
        backend = self.backend_registry.get_backend(backend_name)
        backend.start(created.job, created.job_data, user=auth_payload)

        logger.info(
            "Started background job %s for %s (backend=%s)",
            created.job.id,
            created.job.job_type,
            backend_name,
        )
        return created.job.id

    def start(
        self,
        auth_payload: dict[str, Any] | None,
        job_type: str,
        args: dict[str, Any] | None = None,
        form_data: dict[str, Any] | None = None,
    ) -> int:
        """Create a job with form data and hand it to the configured backend. Returns the job id."""
        return self._dispatch(
            auth_payload,
            job_type,
            args,
            form_data,
        )

    def run_now(
        self,
        job_type: str,
        args: dict[str, Any] | None = None,
        user: dict[str, Any] | None = None,
        *,
        install_signal_handlers: bool = True,
    ) -> int:
        """Create a job and run it synchronously in the current process.

        Intended for CLI/background jobs that need no user token. ``user`` defaults to the
        system user. Returns the executor exit code (0 = success).
        """
        user = user or system_user()
        created = self.creator.create(
            username=user["username"],
            job_type=job_type,
            backend_name=INLINE_BACKEND_NAME,
            args=args,
        )
        logger.info("Running job %s (%s) inline", created.job.id, job_type)
        return self.executor.run(
            created.job.id,
            user=user,
            install_signal_handlers=install_signal_handlers,
        )


__all__ = [
    "INLINE_BACKEND_NAME",
    "JobStarter",
]
