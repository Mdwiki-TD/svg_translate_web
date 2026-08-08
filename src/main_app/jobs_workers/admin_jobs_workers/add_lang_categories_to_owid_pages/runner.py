"""
Runner module for add_lang_categories_to_owid_pages.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import AddLangCategoriesWorker

logger = logging.getLogger(__name__)


from ...objects import JobsRunner


def add_lang_categories_to_owid_pages_entry(
    data: JobsRunner,
) -> None:
    """Background worker entry-point."""
    logger.info("Starting job %s: add language categories to OWID pages", data.job_id)
    worker = AddLangCategoriesWorker(
        job_id=data.job_id,
        user=data.user,
        cancel_event=data.cancel_event,
        args=data.args,
    )
    worker.run()


__all__ = [
    "add_lang_categories_to_owid_pages_entry",
]
