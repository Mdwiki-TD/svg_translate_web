"""
Background job definitions and registry.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler

from ..jobs_workers import jobs_worker

logger = logging.getLogger(__name__)


@dataclass
class BackgroundJob:
    """Job configuration and runtime state."""

    id: str
    hour: int
    minute: int
    func: callable
    job_scheduler: Any = field(default=None, repr=False)


def collect_main_files_job() -> None:
    """Scheduled job to collect main files."""
    logger.info("Starting scheduled collect_main_files job")
    try:
        job_id = jobs_worker.start_job(user=None, job_type="collect_main_files")
        logger.info(f"Scheduled collect_main_files job started with ID {job_id}")
    except Exception:
        logger.exception("Failed to start scheduled collect_main_files job")


# Job registry - dictionary for O(1) lookup by job_id
jobs_data: dict[str, BackgroundJob] = {
    "collect_main_files_daily": BackgroundJob(
        id="collect_main_files_daily",
        hour=3,
        minute=0,
        func=collect_main_files_job,
    )
}


def get_all_jobs_info(scheduler: BackgroundScheduler | None) -> list[dict]:
    """Get information about all scheduled jobs."""

    result = []
    for job_id, job in jobs_data.items():
        info = {
            "id": job.id,
            "hour": job.hour,
            "minute": job.minute,
            "last_run": None,
            "next_run": None,
        }
        if job.job_scheduler is not None:
            info["next_run"] = job.job_scheduler.next_run_time
            # Get last run time from scheduler's job store
            try:
                scheduler_job = scheduler.get_job(job_id) if scheduler else None
                if scheduler_job and hasattr(scheduler_job, "last_run_time"):
                    info["last_run"] = scheduler_job.last_run_time
            except JobLookupError:
                pass
        result.append(info)
    return result
