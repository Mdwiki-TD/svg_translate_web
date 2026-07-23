"""
Runner module for add_lang_categories_to_owid_pages.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import AddLangCategoriesWorker

logger = logging.getLogger(__name__)


def add_lang_categories_to_owid_pages_entry(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point.

    Args:
        job_id: The job ID
        user: User authentication data
        cancel_event: Threading event for cancellation
        args: Optional arguments dict (supports ``limit_items``)
    """
    logger.info("Starting job %s: add language categories to OWID pages", job_id)
    worker = AddLangCategoriesWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "add_lang_categories_to_owid_pages_entry",
]
