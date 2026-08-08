"""
runner module for collecting main files for templates.
"""

from __future__ import annotations

import logging

from ...objects import JobsRunner
from .worker import CollectMainFilesWorker

logger = logging.getLogger(__name__)


def collect_templates_data_entry(data: JobsRunner) -> None:
    """
    Background worker to collect templates data.

    By default only processes templates missing data. Pass args={"update_all": "true"}
    to re-fetch and update ALL templates.
    """

    logger.info(f"Starting job {data.job_id}: collect templates data")
    worker = CollectMainFilesWorker(data)
    worker.run()


__all__ = [
    "collect_templates_data_entry",
]
