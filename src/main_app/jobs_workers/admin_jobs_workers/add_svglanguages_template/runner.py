"""
Runner module for add_svglanguages_template.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from .worker import AddSvgSVGLanguagesTemplate

logger = logging.getLogger(__name__)


def add_svglanguages_template_to_templates(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """
    Background worker

    Args:
        job_id: The job ID
        user: User authentication data
        cancel_event: Threading event for cancellation
        args: Optional arguments dict (unused, for unified signature)
    """
    logger.info("Starting job %s: add {{SVGLanguages|...}} template to templates pages.", job_id)

    worker = AddSvgSVGLanguagesTemplate(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "add_svglanguages_template_to_templates",
]
