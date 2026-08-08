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
    data: JobsRunner | None = None,
    *,
    job_id: int | None = None,
    user: dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
    form_data: dict[str, Any] | None = None,
) -> None:
    """Entry point for the background job."""
    if data is not None:
        job_id = data.job_id
        user = data.user
        cancel_event = data.cancel_event
        args = data.args
        form_data = data.form_data

    worker = FixNestedJobsProcessor(
        job_id=job_id,  # type: ignore
        user=user,      # type: ignore
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "fix_nested_jobs_worker_entry",
]
