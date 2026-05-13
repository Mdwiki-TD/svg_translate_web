"""Service for managing background jobs."""

from __future__ import annotations

import logging

from ..config import settings
from ..db import has_db_config
from ..db.db_Jobs import JobRecord, JobsDB

logger = logging.getLogger(__name__)

_JOBS_STORE: JobsDB | None = None


def get_jobs_db() -> JobsDB:
    """
    Return the singleton JobsDB instance used by the module, creating it if necessary.

    Creates and caches a JobsDB initialized from settings.database_data on first call.

    Returns:
        JobsDB: The singleton jobs database instance.

    Raises:
        RuntimeError: If no database configuration is available or if JobsDB initialization fails.
    """
    global _JOBS_STORE

    if _JOBS_STORE is None:
        if not has_db_config():
            raise RuntimeError("Jobs administration requires database configuration; no fallback store is available.")

        try:
            _JOBS_STORE = JobsDB(settings.database_data)
        except Exception as exc:  # pragma: no cover - defensive guard for startup failures
            logger.exception("Failed to initialize MySQL jobs store")
            raise RuntimeError("Unable to initialize jobs store") from exc

    return _JOBS_STORE


def create_job(job_type: str, username: str | None = None) -> JobRecord:
    """Create a new job."""
    store = get_jobs_db()
    return store.create(job_type, username)


def get_job(job_id: int, job_type: str) -> JobRecord:
    """Get a job by ID."""
    store = get_jobs_db()
    return store.get(job_id, job_type)


def delete_job(job_id: int, job_type: str) -> None:
    """Delete a job by ID and job type."""
    store = get_jobs_db()
    store.delete(job_id, job_type)


def list_jobs(limit: int = 100, job_type: str | None = None) -> list[JobRecord]:
    """list recent jobs, optionally filtered by job_type."""
    store = get_jobs_db()
    return store.list(limit=limit, job_type=job_type)


def update_job_status(job_id: int, status: str, result_file: str | None = None, *, job_type: str) -> JobRecord:
    """Update job status."""
    store = get_jobs_db()
    return store.update_status(job_id, status, result_file, job_type=job_type)


def cancel_job(job_id: int, job_type: str | None = None) -> bool:
    """Mark a job as cancelled."""
    store = get_jobs_db()
    return store.cancel(job_id, job_type)


def is_job_cancelled(job_id: int, job_type: str) -> bool:
    """Check if a job is marked as cancelled."""
    store = get_jobs_db()
    return store.is_cancelled(job_id, job_type)


__all__ = [
    "create_job",
    "get_job",
    "list_jobs",
    "update_job_status",
    "cancel_job",
    "is_job_cancelled",
    "delete_job",
]
