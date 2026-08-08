"""
runner module for collecting main files for templates.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import CollectMainFilesWorker

logger = logging.getLogger(__name__)


from ...objects import JobsRunner


def collect_templates_data_entry(
    data: JobsRunner | None = None,
    *,
    job_id: int | None = None,
    user: dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
    form_data: dict[str, Any] | None = None,
) -> None:
    """
    Background worker to collect templates data.

    By default only processes templates missing data. Pass args={"update_all": "true"}
    to re-fetch and update ALL templates.
    """
    if data is not None:
        job_id = data.job_id
        user = data.user
        cancel_event = data.cancel_event
        args = data.args
        form_data = data.form_data

    logger.info(f"Starting job {job_id}: collect templates data")
    worker = CollectMainFilesWorker(
        job_id=job_id,  # type: ignore
        user=user,      # type: ignore
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "collect_templates_data_entry",
]
