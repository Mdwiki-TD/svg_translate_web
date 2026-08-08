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
    data: JobsRunner,
) -> None:
    """
    Background worker
    """
    logger.info("Starting job %s: add {{SVGLanguages|...}} template to templates pages.", data.job_id)

    worker = AddSvgSVGLanguagesTemplate(
        job_id=data.job_id,
        user=data.user,
        cancel_event=data.cancel_event,
        args=data.args,
    )
    worker.run()


__all__ = [
    "add_svglanguages_template_to_templates",
]
