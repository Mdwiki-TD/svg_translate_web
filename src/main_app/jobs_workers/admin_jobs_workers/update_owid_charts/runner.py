"""
Runner module for update_owid_charts.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import UpdateOwidChartsWorker

logger = logging.getLogger(__name__)


from ...objects import JobsRunner


def update_owid_charts_worker_entry(
    data: JobsRunner,
) -> None:
    """Background worker entry-point for update_owid_charts."""
    logger.info("Starting job %s: update OWID charts timespan data", data.job_id)

    worker = UpdateOwidChartsWorker(
        job_id=data.job_id,
        user=data.user,
        cancel_event=data.cancel_event,
        args=data.args,
    )
    worker.run()


__all__ = [
    "update_owid_charts_worker_entry",
]
