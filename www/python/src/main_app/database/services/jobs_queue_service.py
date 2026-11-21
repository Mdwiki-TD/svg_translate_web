from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db_base import db
from ..models import JobRecord
from .crud_service import CRUDService

logger = logging.getLogger(__name__)


class QueueJobsService(CRUDService[JobRecord]):
    model = JobRecord

    FINAL_STATUSES = ("completed", "failed", "cancelled", "skipped")

    # Status of a job that is accepted and waiting for its turn in the queue.
    PENDING_STATUS = "pending"

    # Status of a job that holds the unique active slot for its job_type.
    RUNNING_STATUS = "running"

    # Grace period (seconds) after which a terminal job that still holds the
    # active slot is considered stale and its slot is released by recovery.
    STALE_SLOT_GRACE_SECONDS = 300

    def __init__(self, session: Session | None = None) -> None:
        super().__init__(session=session or db.session)

    # ------------------------------------------------------------------
    # Queue primitives
    # ------------------------------------------------------------------

    def enqueue_job(self, job_type: str, username: str) -> JobRecord:
        """Create a queued job record without reserving the active slot.

        The row is written with ``status='pending'`` and ``is_running=NULL`` so
        that any number of jobs of the same type can wait in the queue. The
        unique ``idx_unique_active_job`` constraint only sees non-NULL values,
        therefore pending rows never conflict with each other.

        Args:
            job_type: The job type identifier.
            username: Owner of the job.

        Returns:
            The persisted pending JobRecord.
        """
        job = JobRecord(
            job_type=job_type,
            username=username,
            status=self.PENDING_STATUS,
            is_running=None,
        )
        try:
            self.session.add(job)
            self.session.commit()
            self.session.refresh(job)
        except Exception:
            self.session.rollback()
            logger.exception("Failed to enqueue job of type %s", job_type)
            raise

        return job

    def claim_pending_job(self, job_id: int) -> bool:
        """Atomically move a pending job to running, reserving the active slot.

        Equivalent SQL::

            UPDATE jobs
               SET status = 'running', is_running = 1, started_at = NOW()
             WHERE id = %s AND status = 'pending' AND is_running IS NULL

        The database unique constraint on ``(job_type, is_running)`` is the
        final guard: when another job of the same type already holds the slot
        the UPDATE raises an IntegrityError, which is reported as a lost claim
        (``False``) instead of an error.

        Args:
            job_id: The pending job to claim.

        Returns:
            True when this caller claimed the job, False when the job was
            already claimed, cancelled, or the slot is taken by another job.
        """
        stmt = (
            update(JobRecord)
            .where(
                JobRecord.id == job_id,
                JobRecord.status == self.PENDING_STATUS,
                JobRecord.is_running.is_(None),
            )
            .values(
                status=self.RUNNING_STATUS,
                is_running=True,
                started_at=func.current_timestamp(),
            )
            .execution_options(synchronize_session=False)
        )
        try:
            result = self.session.execute(stmt)
            self.session.commit()
            # Bulk UPDATEs bypass the identity map: drop cached state so later
            # reads see the committed values (session uses expire_on_commit=False).
            self.session.expire_all()
        except IntegrityError:
            # Another job of the same type holds idx_unique_active_job.
            self.session.rollback()
            logger.info("Claim race lost for job %s: active slot already taken", job_id)
            return False
        except Exception:
            self.session.rollback()
            logger.exception("Failed to claim pending job %s", job_id)
            return False

        return bool(result.rowcount and result.rowcount > 0)

    def has_running_job(self, job_type: str) -> bool:
        """Return True when a job of ``job_type`` currently holds the active slot."""
        try:
            row = (
                self.session.query(JobRecord.id)
                .filter(JobRecord.job_type == job_type, JobRecord.is_running == 1)
                .first()
            )
            return row is not None
        except Exception:
            self.session.rollback()
            logger.exception("Error checking for a running job of type %s", job_type)
            return False

    def list_pending_jobs(self, job_type: str | None = None, limit: int | None = None) -> list[JobRecord]:
        """List queued jobs in FIFO order (``created_at ASC, id ASC``).

        Args:
            job_type: Restrict the listing to a single job type.
            limit: Optional maximum number of rows.

        Returns:
            Pending jobs that do not hold the active slot, oldest first.
        """
        query = self.session.query(JobRecord).filter(
            JobRecord.status == self.PENDING_STATUS,
            JobRecord.is_running.is_(None),
        )
        if job_type:
            query = query.filter(JobRecord.job_type == job_type)

        query = query.order_by(JobRecord.created_at.asc(), JobRecord.id.asc())
        if limit is not None and limit > 0:
            query = query.limit(limit)

        try:
            return list(query.all())
        except Exception:
            self.session.rollback()
            logger.exception("Error listing pending jobs")
            return []

    def list_pending_job_types(self) -> list[str]:
        """Return the distinct job types that currently have queued jobs."""
        try:
            rows = (
                self.session.query(JobRecord.job_type)
                .filter(
                    JobRecord.status == self.PENDING_STATUS,
                    JobRecord.is_running.is_(None),
                )
                .distinct()
                .all()
            )
            return [row[0] for row in rows]
        except Exception:
            self.session.rollback()
            logger.exception("Error listing pending job types")
            return []

    def get_queue_position(self, job_id: int) -> int:
        """Return the 1-based FIFO position of a pending job inside its type.

        Args:
            job_id: The queued job.

        Returns:
            The position (1 = next to run), or 0 when the job is not queued.
        """
        job = self.get_record_by_id(job_id)
        if job is None:
            return 0

        return self._position_in(job)

    def get_queue_positions(self, job_type: str) -> dict[int, int]:
        """Map every pending job id of ``job_type`` to its 1-based position."""
        pending = self.list_pending_jobs(job_type)
        return {job.id: index + 1 for index, job in enumerate(pending)}

    def _position_in(self, job: JobRecord) -> int:
        if (job.status or "").lower() != self.PENDING_STATUS or job.is_running is not None:
            return 0

        pending = self.list_pending_jobs(job.job_type)
        for index, candidate in enumerate(pending):
            if candidate.id == job.id:
                return index + 1
        return 0

    def cancel_pending_job(self, job_id: int, job_type: str | None = None) -> bool:
        """Cancel a job that has not started yet.

        Only rows that are still queued (``status='pending'`` and no active
        slot) are affected, so a job that was claimed concurrently is never
        cancelled by mistake.

        Args:
            job_id: The queued job.
            job_type: Optional extra filter.

        Returns:
            True when the pending job was cancelled.
        """
        stmt = (
            update(JobRecord)
            .where(
                JobRecord.id == job_id,
                JobRecord.status == self.PENDING_STATUS,
                JobRecord.is_running.is_(None),
            )
            .values(status="cancelled", completed_at=func.current_timestamp())
            .execution_options(synchronize_session=False)
        )
        if job_type:
            stmt = stmt.where(JobRecord.job_type == job_type)

        try:
            result = self.session.execute(stmt)
            self.session.commit()
            # Bulk UPDATEs bypass the identity map: drop cached state so later
            # reads see the committed values (session uses expire_on_commit=False).
            self.session.expire_all()
        except Exception:
            self.session.rollback()
            logger.exception("Error cancelling pending job %s", job_id)
            return False

        return bool(result.rowcount and result.rowcount > 0)

    def release_active_slot(self, job_id: int) -> bool:
        """Release the unique active slot held by ``job_id`` without touching status."""
        stmt = (
            update(JobRecord)
            .where(JobRecord.id == job_id, JobRecord.is_running == 1)
            .values(is_running=None)
            .execution_options(synchronize_session=False)
        )
        try:
            result = self.session.execute(stmt)
            self.session.commit()
            # Bulk UPDATEs bypass the identity map: drop cached state so later
            # reads see the committed values (session uses expire_on_commit=False).
            self.session.expire_all()
        except Exception:
            self.session.rollback()
            logger.exception("Error releasing the active slot of job %s", job_id)
            return False

        return bool(result.rowcount and result.rowcount > 0)

    def fail_job(self, job_id: int, job_type: str, message: str = "") -> bool:
        """Mark a job as failed, store the reason, and release the active slot.

        Args:
            job_id: Target job.
            job_type: Job type used for logging and validation.
            message: Non-sensitive human readable failure reason.

        Returns:
            True when the job was updated.
        """
        stmt = (
            update(JobRecord)
            .where(JobRecord.id == job_id, JobRecord.job_type == job_type)
            .values(
                status="failed",
                is_running=None,
                error_message=message or None,
                completed_at=func.current_timestamp(),
            )
            .execution_options(synchronize_session=False)
        )
        try:
            result = self.session.execute(stmt)
            self.session.commit()
            # Bulk UPDATEs bypass the identity map: drop cached state so later
            # reads see the committed values (session uses expire_on_commit=False).
            self.session.expire_all()
        except Exception:
            self.session.rollback()
            logger.exception("Error marking job %s as failed", job_id)
            return False

        return bool(result.rowcount and result.rowcount > 0)

    def release_stale_active_slots(self, grace_seconds: int | None = None) -> int:
        """Release active slots still held by jobs in a terminal state.

        A terminal job normally releases its own slot. The slot can survive
        when a worker process disappeared while a cancellation was in flight.
        Rows are only touched after ``grace_seconds`` so a worker that is still
        winding down in another process is never overlapped.

        Args:
            grace_seconds: Minimum age of ``updated_at``; defaults to
                ``STALE_SLOT_GRACE_SECONDS``.

        Returns:
            Number of released slots.
        """
        grace = self.STALE_SLOT_GRACE_SECONDS if grace_seconds is None else grace_seconds
        cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=grace)

        stmt = (
            update(JobRecord)
            .where(
                JobRecord.is_running == 1,
                JobRecord.status.in_(self.FINAL_STATUSES),
                func.coalesce(JobRecord.updated_at, JobRecord.created_at) < cutoff,
            )
            .values(is_running=None)
            .execution_options(synchronize_session=False)
        )
        try:
            result = self.session.execute(stmt)
            self.session.commit()
            # Bulk UPDATEs bypass the identity map: drop cached state so later
            # reads see the committed values (session uses expire_on_commit=False).
            self.session.expire_all()
        except Exception:
            self.session.rollback()
            logger.exception("Failed to release stale active slots")
            return 0

        released = int(result.rowcount or 0)
        if released:
            logger.info("Released %d stale active slot(s) held by terminal jobs", released)
        return released


__all__ = [
    "QueueJobsService",
]
