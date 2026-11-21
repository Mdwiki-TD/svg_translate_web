"""Worker module for managing background jobs."""

from __future__ import annotations

import logging

from ...database.models import JobRecord
from ...database.services import JobsService
from ...io.jobs_files_service import JobFilesService
from .cancel_registry import get_cancel_event
from .jobs_queue import JobsQueue

logger = logging.getLogger(__name__)


class JobCanceller:
    """Manages cancelling queued and running jobs."""

    def __init__(
        self,
        jobs_files_service: JobFilesService | None = None,
        jobs_service: JobsService | None = None,
        jobs_queue: JobsQueue | None = None,
    ) -> None:
        """Initialize with optional dependencies.

        Args:
            jobs_files_service: Job files service. Falls back to default if None.
            jobs_service: Jobs service. Falls back to default if None.
            jobs_queue: Queue used to cancel jobs that never started.
        """
        self.jobs_files_service = jobs_files_service or JobFilesService()
        self.jobs_service = jobs_service or JobsService()
        self.jobs_queue = jobs_queue or JobsQueue(jobs_service=self.jobs_service)

    def cancel(
        self,
        job_id: int,
        job_type: str | None = None,
        job: JobRecord | None = None,
    ) -> bool:
        """
        Cancel a queued or running job.
        Works across multiple processes by updating the database status.
        Returns True if the job was found and cancellation was requested.
        """
        # Queued jobs never reached a backend: cancel them directly so they are
        # skipped by the dispatcher, without touching cancel events or files.
        if self._is_pending(job_id, job_type, job):
            cancelled = self.jobs_queue.cancel_pending(job_id, job_type)
            if cancelled:
                logger.info("Cancelled queued job %s before it started", job_id)
            return cancelled

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

        # 3. Persist cancellation to DB (for cross-process detection).
        #    A running job keeps its active slot until its execution really
        #    stopped, so the next queued job can never overlap it.
        try:
            db_cancelled = self.jobs_service.cancel_job_db(job_id, job_type)
            if db_cancelled:
                logger.info(f"Database cancellation requested for job {job_id}")

        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Failed to cancel job %s in database.", job_id)
            db_cancelled = False

        return local_cancelled or cancelled_file is not None or db_cancelled

    def _is_pending(
        self,
        job_id: int,
        job_type: str | None,
        job: JobRecord | None,
    ) -> bool:
        """Return True when the job is still queued (never dispatched)."""
        record = job
        if record is None:
            try:
                record = self.jobs_service.get_record_by_id(job_id)
            except Exception:  # pragma: no cover - defensive guard
                logger.exception("Failed to load job %s for cancellation", job_id)
                return False

        if record is None:
            return False

        if job_type and record.job_type != job_type:
            return False

        return (record.status or "").lower() == "pending" and record.is_running is None


cancel_job_worker = JobCanceller().cancel

__all__ = [
    "cancel_job_worker",
    "JobCanceller",
]
