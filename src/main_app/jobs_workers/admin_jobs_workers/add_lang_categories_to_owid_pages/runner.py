"""
Runner module for add_lang_categories_to_owid_pages.
"""

from __future__ import annotations

import logging

from ...objects import JobsRunner
from .worker import AddLangCategoriesWorker

logger = logging.getLogger(__name__)


def add_lang_categories_to_owid_pages_entry(data: JobsRunner) -> None:
    """Background worker entry-point."""
    logger.info("Starting job %s: add language categories to OWID pages", data.job_id)
    worker = AddLangCategoriesWorker(data)
    worker.run()


__all__ = [
    "add_lang_categories_to_owid_pages_entry",
]
