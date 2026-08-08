"""
Worker module for fixing nested tags in main files of templates.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import FixNestedMainFilesWorker

logger = logging.getLogger(__name__)


from ...objects import JobsRunner


def fix_nested_main_files_for_templates(
    data: JobsRunner | None = None,
    *,
    job_id: int | None = None,
    user: dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
    form_data: dict[str, Any] | None = None,
) -> None:
    """
    Background worker to run fix_nested task on all main files from templates.
    """
    if data is not None:
        job_id = data.job_id
        user = data.user
        cancel_event = data.cancel_event
        args = data.args
        form_data = data.form_data

    logger.info("Starting job %s: fix nested tags for template main files", job_id)
    worker = FixNestedMainFilesWorker(job_id, user, cancel_event, args)  # type: ignore
    worker.run()


__all__ = [
    "fix_nested_main_files_for_templates",
]
