from __future__ import annotations

import logging
from datetime import UTC, datetime

from ...extensions import db
from ..models.jobs import JobRecord

logger = logging.getLogger(__name__)


def create_job(job_type: str, username: str | None = None) -> JobRecord:
    """
    Create a new job record.

    Query to match:
        INSERT INTO jobs (job_type, status, username) VALUES (%s, %s, %s)
        (job_type, "pending", username),
    """
    job = JobRecord(job_type=job_type, username=username, status="pending")
    db.session.add(job)
    db.session.commit()
    db.session.refresh(job)
    return job


def get_job(job_id: int, job_type: str) -> JobRecord:
    """
    Get a job by ID.

    def get(self, job_id: int, job_type: str = "fix_nested_main_files") -> JobRecord:
        rows = self.db.fetch_query_safe(
            '''
            SELECT id, job_type, username, status, started_at, completed_at, result_file, created_at, updated_at
            FROM jobs
            WHERE id = %s AND job_type = %s
            ''',
            (job_id, job_type),
        )
        if not rows:
            raise LookupError(f"Job id {job_id} was not found")
        return self._row_to_record(rows[0])
    """
    query = db.session.query(JobRecord).filter(JobRecord.id == job_id)
    if job_type:
        query = query.filter(JobRecord.job_type == job_type)
    job = query.first()
    if not job:
        raise LookupError(f"Job id {job_id} was not found")
    return job


def update_running_status(job_id: int, result_file: str | None = None, *, job_type: str) -> JobRecord:
    """
    Update running job status and optional result file.
    """
    job = db.session.query(JobRecord).filter(JobRecord.id == job_id, JobRecord.job_type == job_type).first()
    if not job:
        raise LookupError(f"Job id {job_id} was not found")

    job.status = "running"
    if not job.started_at:
        job.started_at = datetime.now(UTC)
    if result_file:
        job.result_file = result_file
    db.session.commit()
    db.session.refresh(job)
    return job


def _update_status(job_id: int, status: str, result_file: str, job_type: str) -> JobRecord:
    """
    Update job status and result file.
    """
    query = db.session.query(JobRecord).filter(JobRecord.id == job_id)
    if job_type:
        query = query.filter(JobRecord.job_type == job_type)
    job = query.first()

    if not job:
        raise LookupError(f"Job id {job_id} was not found")

    job.status = status
    if status in ("completed", "failed", "cancelled"):
        job.completed_at = datetime.now(UTC)
    if result_file:
        job.result_file = result_file
    db.session.commit()
    db.session.refresh(job)

    return job


def update_job_status(job_id: int, status: str, result_file: str | None = None, *, job_type: str) -> JobRecord:
    """
    Update job status and optional result file.

    Query to match:

    """
    if status == "running":
        return update_running_status(job_id, result_file, job_type=job_type)

    return _update_status(job_id, status, result_file, job_type)


def list_jobs(limit: int = 100, job_type: str | None = None) -> list[JobRecord]:
    """
    list recent jobs, optionally filtered by job_type.

    Query to match:
        if job_type:
            SELECT id, job_type, username, status, started_at, completed_at, result_file, created_at, updated_at
            FROM jobs
            WHERE job_type = %s
            ORDER BY created_at DESC
            LIMIT %s
        else:
            SELECT id, job_type, username, status, started_at, completed_at, result_file, created_at, updated_at
            FROM jobs
            ORDER BY created_at DESC
            LIMIT %s
    """
    query = db.session.query(JobRecord)
    if job_type:
        query = query.filter(JobRecord.job_type == job_type)
    return query.order_by(JobRecord.created_at.desc()).limit(limit).all()


def delete_job(job_id: int, job_type: str) -> bool:
    """
    Delete a job by ID and job type.

    Code to match:
        query = "DELETE FROM jobs WHERE id = %s AND job_type = %s"
        try:
            self.db.execute_query_safe(query, (job_id, job_type))
            return True
        except Exception as e:
            logger.exception(f"Failed to delete job id {job_id} of type {job_type}: {e}")
            return False
    """
    record = db.session.query(JobRecord).filter(JobRecord.id == job_id, JobRecord.job_type == job_type).first()
    if not record:
        return False
    db.session.delete(record)
    db.session.commit()
    return True


def cancel_job(job_id: int, job_type: str | None = None) -> bool:
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
    query = db.session.query(JobRecord).filter(JobRecord.id == job_id)
    if job_type:
        query = query.filter(JobRecord.job_type == job_type)

    job = query.filter(JobRecord.status.in_(["pending", "running"])).first()

    if job:
        job.status = "cancelled"
        job.completed_at = datetime.now(UTC)
        db.session.commit()
        db.session.refresh(job)
        return True
    return False


def is_job_cancelled(job_id: int, job_type: str) -> bool:
    """
    Check if a job is marked as cancelled.

    Query to match:
        SELECT status FROM jobs WHERE id = %s AND job_type = %s
    """
    record = db.session.query(JobRecord).filter(JobRecord.id == job_id, JobRecord.job_type == job_type).first()
    if record:
        return record.status == "cancelled"
    return False


__all__ = [
    "create_job",
    "get_job",
    "list_jobs",
    "update_job_status",
    "update_running_status",
    "cancel_job",
    "is_job_cancelled",
    "delete_job",
]
