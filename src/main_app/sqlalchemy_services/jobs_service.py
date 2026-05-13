from __future__ import annotations

import logging
from typing import List, Optional
from datetime import datetime

from ..sqlalchemy_models.jobs import JobRecord
from ..engine import get_session

logger = logging.getLogger(__name__)


def create_job(job_type: str, username: Optional[str] = None) -> JobRecord:
    """Create a new job record."""
    with get_session() as session:
        job = JobRecord(job_type=job_type, username=username, status="pending")
        session.add(job)
        session.commit()
        session.refresh(job)
        return job


def get_job(job_id: int) -> Optional[JobRecord]:
    """Fetch a job by ID."""
    with get_session() as session:
        return session.query(JobRecord).filter(JobRecord.id == job_id).first()


def update_job_status(job_id: int, status: str, result_file: Optional[str] = None) -> Optional[JobRecord]:
    """Update job status and optional result file."""
    with get_session() as session:
        job = session.query(JobRecord).filter(JobRecord.id == job_id).first()
        if job:
            job.status = status
            if status == "running" and not job.started_at:
                job.started_at = datetime.utcnow()
            if status in ("completed", "failed"):
                job.completed_at = datetime.utcnow()
            if result_file:
                job.result_file = result_file
            session.commit()
            session.refresh(job)
        return job


def list_jobs(limit: int = 100) -> List[JobRecord]:
    """List recent jobs."""
    with get_session() as session:
        return session.query(JobRecord).order_by(JobRecord.created_at.desc()).limit(limit).all()


__all__ = [
    "create_job",
    "get_job",
    "update_job_status",
    "list_jobs",
]
