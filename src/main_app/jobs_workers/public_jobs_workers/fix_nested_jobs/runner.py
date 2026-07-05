"""
Worker module for fix_nested_jobs.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import FixNestedJobsProcessor

logger = logging.getLogger(__name__)


# --- main pipeline --------------------------------------------
def fix_nested_jobs_worker_entry(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """Entry point for the background job."""

    worker = FixNestedJobsProcessor(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "fix_nested_jobs_worker_entry",
]
