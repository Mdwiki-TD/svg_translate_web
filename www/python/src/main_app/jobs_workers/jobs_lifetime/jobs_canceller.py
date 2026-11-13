"""Worker module for managing background jobs."""

from __future__ import annotations

import logging

from ...database.models import JobRecord
from ...database.services import JobsService
from ...io.jobs_files_service import JobFilesService
from .cancel_registry import get_cancel_event

logger = logging.getLogger(__name__)


class JobCanceller:
    """Manages cancelling running jobs."""

    def __init__(
        self,
        jobs_files_service: JobFilesService | None = None,
        jobs_service: JobsService | None = None,
    ) -> None:
        """Initialize with optional dependencies.

        Args:
            jobs_files_service: Job files service. Falls back to default if None.
            jobs_service: Jobs service. Falls back to default if None.
        """
        self.jobs_files_service = jobs_files_service or JobFilesService()
        self.jobs_service = jobs_service or JobsService()

    def cancel(
        self,
        job_id: int,
        job_type: str | None = None,
        job: JobRecord | None = None,
    ) -> bool:
        """
        Cancel a running job.
        Works across multiple processes by updating the database status.
        Returns True if the job was found and cancellation was requested.
        """
        # if job is None: job = svc.get_by(id=job_id)

        # 1. Try local cancellation (if the job is in this process)
        cancel_event = get_cancel_event(job_id)
        local_cancelled = False
        if cancel_event:
            cancel_event.set()
            logger.info(f"Local cancellation requested for job {job_id}")
            local_cancelled = True

        cancelled_file = None
        # 2. Create result_file_cancelled file
        if job and job.result_file:
            cancelled_file = self.jobs_files_service.create_cancel_file(f"{job.result_file}.cancelled")

        # 3. Persist cancellation to DB (for cross-process detection)
        try:
            db_cancelled = self.jobs_service.cancel_job_db(job_id, job_type)
            if db_cancelled:
                logger.info(f"Database cancellation requested for job {job_id}")

        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Failed to cancel job %s in database.", job_id)
            db_cancelled = False

        return local_cancelled or cancelled_file is not None or db_cancelled


cancel_job_worker = JobCanceller().cancel

__all__ = [
    "cancel_job_worker",
    "JobCanceller",
]
