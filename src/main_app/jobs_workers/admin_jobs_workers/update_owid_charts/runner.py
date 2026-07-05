"""
Runner module for update_owid_charts.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import UpdateOwidChartsWorker

logger = logging.getLogger(__name__)


def update_owid_charts_worker_entry(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point for update_owid_charts."""
    logger.info("Starting job %s: update OWID charts timespan data", job_id)

    worker = UpdateOwidChartsWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "update_owid_charts_worker_entry",
]
