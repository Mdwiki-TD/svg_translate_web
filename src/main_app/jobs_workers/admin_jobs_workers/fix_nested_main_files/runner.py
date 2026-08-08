"""
Worker module for fixing nested tags in main files of templates.
"""

from __future__ import annotations

import logging

from ...objects import JobsRunner
from .worker import FixNestedMainFilesWorker

logger = logging.getLogger(__name__)


def fix_nested_main_files_for_templates(data: JobsRunner) -> None:
    """
    Background worker to run fix_nested task on all main files from templates.
    """
    logger.info("Starting job %s: fix nested tags for template main files", data.job_id)
    worker = FixNestedMainFilesWorker(
        data.job_id,
        data.user,
        data.cancel_event,
        data.args,
    )
    worker.run()


__all__ = [
    "fix_nested_main_files_for_templates",
]
