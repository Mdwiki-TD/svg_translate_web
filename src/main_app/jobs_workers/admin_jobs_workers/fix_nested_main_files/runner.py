"""
Worker module for fixing nested tags in main files of templates.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import FixNestedMainFilesWorker

logger = logging.getLogger(__name__)


def fix_nested_main_files_for_templates(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """
    Background worker to run fix_nested task on all main files from templates.

    Args:
        job_id: The job ID
        user: User authentication data for OAuth uploads
        cancel_event: Optional event to check for cancellation
        args: Optional arguments dict (unused, for unified signature)
    """
    logger.info("Starting job %s: fix nested tags for template main files", job_id)
    worker = FixNestedMainFilesWorker(job_id, user, cancel_event, args)
    worker.run()


__all__ = [
    "fix_nested_main_files_for_templates",
]
