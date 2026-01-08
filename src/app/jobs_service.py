"""Service for managing background jobs."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .config import settings
from .db import has_db_config
from .db.db_Jobs import JobRecord, JobsDB

logger = logging.getLogger("svg_translate")

_JOBS_STORE: JobsDB | None = None


def get_jobs_db() -> JobsDB:
    """Get or create the jobs database instance."""
    global _JOBS_STORE

    if _JOBS_STORE is None:
        if not has_db_config():
            raise RuntimeError(
                "Jobs administration requires database configuration; no fallback store is available."
            )

        try:
            _JOBS_STORE = JobsDB(settings.db_data)
        except Exception as exc:  # pragma: no cover - defensive guard for startup failures
            logger.exception("Failed to initialize MySQL jobs store")
            raise RuntimeError("Unable to initialize jobs store") from exc

    return _JOBS_STORE


def get_jobs_data_dir() -> Path:
    """Get the directory for storing job data files."""
    # Use log_dir from settings paths
    log_dir = getattr(settings.paths, "log_dir", None)
    if not log_dir:
        raise RuntimeError(
            "LOG_PATH environment variable is required for job result storage"
        )
    jobs_dir = Path(log_dir) / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    return jobs_dir


def create_job(job_type: str) -> JobRecord:
    """Create a new job."""
    store = get_jobs_db()
    return store.create(job_type)


def get_job(job_id: int) -> JobRecord:
    """Get a job by ID."""
    store = get_jobs_db()
    return store.get(job_id)


def list_jobs(limit: int = 100) -> List[JobRecord]:
    """List recent jobs."""
    store = get_jobs_db()
    return store.list(limit=limit)


def update_job_status(
    job_id: int, status: str, result_file: str | None = None
) -> JobRecord:
    """Update job status."""
    store = get_jobs_db()
    return store.update_status(job_id, status, result_file)


def save_job_result(job_id: int, result_data: Dict[str, Any]) -> str:
    """Save job result to a JSON file and return the file path."""
    jobs_dir = get_jobs_data_dir()
    filename = f"job_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = jobs_dir / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, default=str)
    
    return str(filepath)


def load_job_result(result_file: str) -> Dict[str, Any] | None:
    """Load job result from a JSON file."""
    if not result_file or not os.path.exists(result_file):
        return None
    
    try:
        with open(result_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading job result from {result_file}: {e}")
        return None


__all__ = [
    "get_jobs_db",
    "create_job",
    "get_job",
    "list_jobs",
    "update_job_status",
    "save_job_result",
    "load_job_result",
    "JobRecord",
]
