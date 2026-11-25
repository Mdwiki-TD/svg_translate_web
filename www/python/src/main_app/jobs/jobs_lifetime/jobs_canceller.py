"""Cancelling running jobs."""

from __future__ import annotations

import logging

from ...database.models import JobRecord
from ...database.services import JobsService
from ...io.jobs_files_service import JobFilesService
from ..backends import BackendRegistry
from ..utils import generate_cancelled_file_name

logger = logging.getLogger(__name__)


class JobCanceller:
    """Cancels a job through every channel that can reach it.

    * Database status: the source of truth, visible to every process.
    * ``.cancelled`` file: read by ``BaseObjectsJobWorker.is_cancelled``; reaches thread jobs
      running in another web process, and pods through the shared mount.
    * Backend: ``ThreadBackend`` sets the in-process event, ``ToolforgeBackend`` deletes the
      pod (the pod then receives SIGTERM, which sets its own cancel event).
    """

    def __init__(
        self,
        jobs_files_service: JobFilesService,
        jobs_service: JobsService | None = None,
        backend_registry: BackendRegistry | None = None,
    ) -> None:
        """Initialize with optional dependencies.

        Args:
            jobs_files_service: Job files service used to create the ``.cancelled`` file.
            jobs_service: Jobs service. Falls back to default if None.
            backend_registry: Backend registry. Falls back to default if None.
        """
        self.jobs_files_service = jobs_files_service
        self.jobs_service = jobs_service or JobsService()
        self.backend_registry = backend_registry or BackendRegistry()

    def cancel(
        self,
        job_id: int,
        job_type: str | None = None,
        job: JobRecord | None = None,
    ) -> bool:
        """Cancel a job. Works across processes.

        Returns True if at least one cancellation channel accepted the request.
        """
        if job is None:
            job = self.jobs_service.get_by(id=job_id)
        if job is not None and job_type is None:
            job_type = job.job_type

        # 1. Persist cancellation to the DB (visible to every process).
        try:
            db_cancelled = bool(self.jobs_service.cancel_job_db(job_id, job_type))
            if db_cancelled:
                logger.info("Database cancellation requested for job %s", job_id)
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Failed to cancel job %s in database.", job_id)
            db_cancelled = False

        if job is None:
            return db_cancelled

        # 2. Create the .cancelled file (even for a job that has no result_file yet).
        cancelled_file = None
        try:
            filename = generate_cancelled_file_name(
                job_id=job.id,
                job_type=job.job_type,
                result_file=job.result_file,
            )

            cancelled_file = self.jobs_files_service.create_cancel_file(filename)
        except Exception:
            logger.exception("Failed to create cancel file for job %s", job_id)

        # 3. Ask the backend that runs the job (thread: set event, toolforge: delete pod).
        backend_cancelled = False
        backend_name = job.backend or "thread"
        try:
            backend = self.backend_registry.get_backend(backend_name)
            backend_cancelled = bool(backend.cancel(job))
        except Exception:
            logger.exception("Failed to cancel job %s on backend '%s'", job_id, backend_name)

        return backend_cancelled or cancelled_file is not None or db_cancelled

    def is_cancelled(
        self,
        job_id: int,
        result_file_cancelled: str,
        check_db: bool = False,
    ) -> bool:
        """Check if a job is cancelled."""

        if self.jobs_files_service.is_cancel_file_exist(result_file_cancelled):
            logger.info("Job %s: Cancelled file detected, stopping.", job_id)
            return True

        # Optimize is_cancelled DB check frequency, by reducing the check frequency (to occur every N cycles).
        if check_db and self.jobs_service.is_job_cancelled(job_id):
            logger.info("Job %s: Global cancellation detected, stopping.", job_id)
            return True

        return False


__all__ = [
    "JobCanceller",
]
