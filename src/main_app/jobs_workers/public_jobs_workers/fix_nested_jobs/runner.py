"""
Worker module for fix_nested_jobs.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import FixNestedJobsProcessor

logger = logging.getLogger(__name__)


from ...objects import JobsRunner


# --- main pipeline --------------------------------------------
def fix_nested_jobs_worker_entry(
    data: JobsRunner,
) -> None:
    """Entry point for the background job."""

    worker = FixNestedJobsProcessor(
        job_id=data.job_id,
        user=data.user,
        cancel_event=data.cancel_event,
        args=data.args,
    )
    worker.run()


__all__ = [
    "fix_nested_jobs_worker_entry",
]
