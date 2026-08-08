"""
Runner module for add_svglanguages_template.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import AddSvgSVGLanguagesTemplate

logger = logging.getLogger(__name__)


from ...objects import JobsRunner


def add_svglanguages_template_to_templates(
    data: JobsRunner | None = None,
    *,
    job_id: int | None = None,
    user: dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
    form_data: dict[str, Any] | None = None,
) -> None:
    """
    Background worker
    """
    if data is not None:
        job_id = data.job_id
        user = data.user
        cancel_event = data.cancel_event
        args = data.args
        form_data = data.form_data

    logger.info("Starting job %s: add {{SVGLanguages|...}} template to templates pages.", job_id)

    worker = AddSvgSVGLanguagesTemplate(
        job_id=job_id,  # type: ignore
        user=user,      # type: ignore
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "add_svglanguages_template_to_templates",
]
