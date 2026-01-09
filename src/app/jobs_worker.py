"""Worker module for collecting main files for templates."""

from __future__ import annotations

import logging
import threading
from typing import Any

from . import jobs_service
from .jobs_workers.collect_main_files_worker import collect_main_files_for_templates
from .jobs_workers.fix_nested_main_files_worker import fix_nested_main_files_for_templates

logger = logging.getLogger("svg_translate")


def start_job(user: Any | None, job_type: str) -> int:
    """
    Start a background job to fix nested tags in all template main files.
    Returns the job ID.

    Args:
        user: User authentication data for OAuth uploads
    """
    jobs_targets = {
        "fix_nested_main_files": fix_nested_main_files_for_templates,
        "collect_main_files": collect_main_files_for_templates,
    }
    if job_type not in jobs_targets:
        raise ValueError(f"Unknown job type: {job_type}")
    # Create job record
    job = jobs_service.create_job(job_type)
    # Start background thread
    thread = threading.Thread(
        target=jobs_targets[job_type],
        args=(job.id, user),
        daemon=True,
    )
    thread.start()

    logger.info(f"Started background job {job.id} for {job_type}")

    return job.id


def start_collect_main_files_job(user: Any | None=None) -> int:
    """
    Start a background job to collect main files for templates.
    Returns the job ID.
    """
    return start_job(user, "collect_main_files")


def start_fix_nested_main_files_job(user: Any | None) -> int:
    """
    Start a background job to fix nested tags in all template main files.
    Returns the job ID.

    Args:
        user: User authentication data for OAuth uploads
    """
    return start_job(user, "fix_nested_main_files")


__all__ = [
    "collect_main_files_for_templates",
    "start_collect_main_files_job",
    "fix_nested_main_files_for_templates",
    "start_fix_nested_main_files_job",
]
