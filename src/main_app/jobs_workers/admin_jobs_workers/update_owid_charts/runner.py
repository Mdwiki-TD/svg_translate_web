"""
Runner module for update_owid_charts.
"""

from __future__ import annotations

import logging

from ...objects import JobsRunner
from .worker import UpdateOwidChartsWorker

logger = logging.getLogger(__name__)


def update_owid_charts_worker_entry(data: JobsRunner) -> None:
    """Background worker entry-point for update_owid_charts."""
    logger.info("Starting job %s: update OWID charts timespan data", data.job_id)

    worker = UpdateOwidChartsWorker(data)
    worker.run()


__all__ = [
    "update_owid_charts_worker_entry",
]
