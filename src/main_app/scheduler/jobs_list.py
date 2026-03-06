"""
"""

from __future__ import annotations
from dataclasses import dataclass
import logging

from ..jobs_workers import jobs_worker
logger = logging.getLogger(__name__)


@dataclass
class BackgroundJob:
    id: str
    hour: int
    minute: int
    func: callable
    upload_host: str
    job_scheduler: None


def collect_main_files_job() -> None:
    """Scheduled job to collect main files."""
    logger.info("Starting scheduled collect_main_files job")
    try:
        job_id = jobs_worker.start_job(user=None, job_type="collect_main_files")
        logger.info(f"Scheduled collect_main_files job started with ID {job_id}")
    except Exception:
        logger.exception("Failed to start scheduled collect_main_files job")


jobs_data = None


def get_job_information(job_id):
    job = None
    # next run time
    next_run = job.job_scheduler.next_run_time
    return next_run
