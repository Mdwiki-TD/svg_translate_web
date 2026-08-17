from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from ...extensions import db
from ..exceptions import DuplicateRecordError
from ..models import JobRecord
from .crud_service import CRUDService
from .utils import retry_on_db_disconnect

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class JobStats:
    """Aggregated counts for a user's jobs."""

    total: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0


@dataclass(frozen=True)
class UserJobsStats:
    """Typed result returned by the user-job statistics queries."""

    stats: JobStats
    recent_jobs: list[JobRecord]

    @classmethod
    def empty(cls) -> UserJobsStats:
        """Return the safe fallback used when statistics cannot be loaded."""
        return cls(stats=JobStats(), recent_jobs=[])


def _normalize_limit(limit: int | None, *, default: int = 100, max_limit: int = 500) -> int:
    if limit is None or limit <= 0:
        return default
    return min(limit, max_limit)


class JobsService(CRUDService[JobRecord]):
    def __init__(self) -> None:
        super().__init__(db.session, JobRecord)

    def is_job_cancelled(self, job_id: int, job_type: str) -> bool:
        """
        Check if a job is marked as cancelled.

        Query to match:
            SELECT status FROM jobs WHERE id = %s AND job_type = %s
        """
        try:
            record = (
                self.session.query(JobRecord).filter(JobRecord.id == job_id, JobRecord.job_type == job_type).first()
            )
            if record:
                # Refresh from database to ensure we don't use a stale cached status
                self.session.refresh(record)
                return (record.status or "").lower() == "cancelled"
            return False
        except Exception as e:
            logger.error(f"Error checking if job {job_id} is cancelled: {e}")
            return False

    def get_job(self, job_id: int, job_type: str) -> JobRecord:
        # return _get_job(job_id, job_type)
        filters = {"id": job_id}
        if job_type:
            filters["job_type"] = job_type

        job = self.get_by(**filters)
        if not job:
            raise LookupError(f"Job id {job_id} was not found")
        return job

    def list_jobs(self, limit: int = 100, job_type: str | None = None) -> list[JobRecord]:
        filters = {}
        if job_type:
            filters["job_type"] = job_type

        return self.list(
            limit=limit,
            filters=filters,
            order_by=[JobRecord.created_at.desc()],
        )

    def get_all_user_jobs_stats(
        self,
        username: str,
        limit: int | None = 100,
    ) -> UserJobsStats:
        return self._get_all_user_jobs_stats(username, limit)

    def get_user_jobs_stats(
        self,
        username: str,
        jobs_types: list | None = None,
        limit: int | None = 100,
    ) -> UserJobsStats:
        """Return typed statistics and recent jobs for the requested job types."""
        if jobs_types is None or not jobs_types:
            return self._get_all_user_jobs_stats(username, limit)

        limit = _normalize_limit(limit)

        base_query = (
            self.session.query(JobRecord)
            .filter(JobRecord.username == username)
            .filter(JobRecord.job_type.in_(jobs_types))
        )

        records = (
            self.session.query(JobRecord.status, func.count(JobRecord.id))
            .filter(JobRecord.username == username)
            .filter(JobRecord.job_type.in_(jobs_types))
            .group_by(JobRecord.status)
            .all()
        )
        status_counts = {row[0]: row[1] for row in records}

        recent_jobs = base_query.order_by(JobRecord.created_at.desc()).limit(limit).all()

        total_jobs = sum(status_counts.values())

        stats = JobStats(
            total=total_jobs,
            completed=status_counts.get("completed", 0),
            failed=status_counts.get("failed", 0),
            cancelled=status_counts.get("cancelled", 0),
        )

        return UserJobsStats(stats=stats, recent_jobs=recent_jobs)

    def has_active_job(self, job_type: str) -> bool:
        """
        Check if there is an active (pending or running) job of the given type.

        This is an auxiliary application-level check that works on all database backends
        (MySQL, SQLite, PostgreSQL). Note that the primary enforcement mechanism for
        preventing duplicate concurrent jobs is the database-level unique constraint
        idx_unique_active_job.
        """
        try:
            result = (
                self.session.query(JobRecord.id)
                .filter(
                    JobRecord.job_type == job_type,
                    JobRecord.status.in_(["pending", "running"]),
                    JobRecord.is_running == 1,
                )
                .first()
            )
            return result is not None
        except Exception as exc:
            logger.exception("Error checking for active job")
            raise exc

    def create_job(self, job_type: str, username: str) -> JobRecord:
        """
        Create a new job record.

        Query to match:
            INSERT INTO jobs (job_type, status, username) VALUES (%s, %s, %s)
            (job_type, "pending", username),

        Raises:
            DuplicateRecordError: If a job of the same type is already running.
        """
        try:
            job = JobRecord(job_type=job_type, username=username, status="pending", is_running=1)
            self.session.add(job)
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            if "idx_unique_active_job" in str(exc.orig) or "UNIQUE constraint failed" in str(exc.orig):
                logger.warning("Duplicate active job detected for job_type=%s", job_type)
                raise DuplicateRecordError(
                    f"A job of type '{job_type}' is already active (pending or running)."
                ) from exc
            raise  # Re-raise unexpected IntegrityError
        self.session.refresh(job)
        return job

    def update_job_status(
        self,
        job_id: int,
        status: str,
        result_file: str | None = None,
        *,
        job_type: str,
    ) -> JobRecord:
        """
        Update job status and result file.
        """
        job = self.get_job(job_id, job_type)
        try:
            return self._update_job_status(job, status, result_file)
        except Exception as exc:
            self.session.rollback()
            raise exc

    def update_job_status_with_retry(
        self,
        job_id: int,
        status: str,
        result_file: str | None = None,
        *,
        job_type: str,
        remove_session: bool = True,
    ) -> JobRecord:
        @retry_on_db_disconnect(remove_session=remove_session)
        def with_retry() -> JobRecord:
            job = self.get_job(job_id, job_type)
            return self._update_job_status(job, status, result_file)

        return with_retry()

    def cancel_job_db(self, job_id: int, job_type: str | None = None) -> bool:
        """
        Mark a job as cancelled.
            query = "UPDATE jobs SET status = 'cancelled', completed_at = NOW() WHERE id = %s AND status IN ('pending', 'running')"
            params = [job_id]
            if job_type:
                query += " AND job_type = %s"
                params.append(job_type)

            rowcount = self.db.execute_query_safe(query, tuple(params))
            return rowcount > 0
        """
        try:
            query = self.session.query(JobRecord).filter(JobRecord.id == job_id)
            if job_type:
                query = query.filter(JobRecord.job_type == job_type)

            job = query.filter(
                JobRecord.status.in_(["pending", "running"]),
                JobRecord.is_running == 1,
            ).first()

            if not job:
                return False

            job.status = "cancelled"

            if job.completed_at is None:
                job.completed_at = datetime.now(UTC)

            job.is_running = None

            self.session.commit()
            self.session.refresh(job)
            return True
        except Exception as e:
            logger.error(f"Error cancelling JobRecord: {e}")
            self.session.rollback()
            return False

    def delete_job_by_id_and_type(self, job_id: int, job_type: str) -> bool:
        """
        Special case since it filters by multiple columns (id and job_type).
        """
        try:
            affected_rows = (
                self.session.query(JobRecord)
                .filter(JobRecord.id == job_id, JobRecord.job_type == job_type)
                .delete(synchronize_session=False)
            )
            self.session.commit()
            return affected_rows > 0
        except Exception as e:
            logger.error(f"Error deleting JobRecord: {e}")
            self.session.rollback()
            return False

    def _update_job_status(
        self,
        job: JobRecord,
        status: str,
        result_file: str | None = None,
    ) -> JobRecord:
        """
        Update job status and result file.
        """

        status_lower = status.lower()
        job.status = status_lower

        if status_lower == "running" and not job.started_at:
            job.started_at = datetime.now(UTC)

        if status_lower in ("completed", "failed", "cancelled", "skipped"):
            job.completed_at = datetime.now(UTC)
            job.is_running = None

        if result_file:
            job.result_file = result_file

        self.session.commit()
        self.session.refresh(job)

        return job

    def _get_all_user_jobs_stats(
        self, username: str, limit: int | None = 100
    ) -> UserJobsStats:
        """Return typed statistics and recent jobs for all of a user's job types."""
        limit = _normalize_limit(limit)

        base_query = self.session.query(JobRecord).filter(JobRecord.username == username)

        records = (
            self.session.query(JobRecord.status, func.count(JobRecord.id))
            .filter(JobRecord.username == username)
            .group_by(JobRecord.status)
            .all()
        )
        status_counts: dict[str, int] = {row[0]: row[1] for row in records}

        recent_jobs = base_query.order_by(JobRecord.created_at.desc()).limit(limit).all()

        total_jobs = sum(status_counts.values())

        stats = JobStats(
            total=total_jobs,
            completed=status_counts.get("completed", 0),
            failed=status_counts.get("failed", 0),
            cancelled=status_counts.get("cancelled", 0),
        )

        return UserJobsStats(stats=stats, recent_jobs=recent_jobs)

    def mark_as_completed(self, job: JobRecord) -> None:
        job.is_running = None
        if job.completed_at is None:
            job.completed_at = datetime.now(UTC)

        self.update(job, status="completed")


__all__ = [
    "JobStats",
    "JobsService",
    "UserJobsStats",
]
