"""
runner module for collecting main files for templates.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import CollectMainFilesWorker

logger = logging.getLogger(__name__)


def collect_templates_data_entry(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """
    Background worker to collect templates data.

    By default only processes templates missing data. Pass args={"update_all": "true"}
    to re-fetch and update ALL templates.

    Args:
        job_id: The job ID
        user: User authentication data
        cancel_event: Threading event for cancellation
        args: Optional arguments dict. Supports:
            - update_all: "true" to update all templates, not just those missing data.
    """

    logger.info(f"Starting job {job_id}: collect templates data")
    worker = CollectMainFilesWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "collect_templates_data_entry",
]
