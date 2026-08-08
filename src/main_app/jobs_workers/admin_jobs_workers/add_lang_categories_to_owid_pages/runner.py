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
    data: JobsRunner | None = None,
    *,
    job_id: int | None = None,
    user: dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
    form_data: dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point."""
    if data is not None:
        job_id = data.job_id
        user = data.user
        cancel_event = data.cancel_event
        args = data.args
        form_data = data.form_data

    logger.info("Starting job %s: add language categories to OWID pages", job_id)
    worker = AddLangCategoriesWorker(
        job_id=job_id,  # type: ignore
        user=user,      # type: ignore
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "add_lang_categories_to_owid_pages_entry",
]
