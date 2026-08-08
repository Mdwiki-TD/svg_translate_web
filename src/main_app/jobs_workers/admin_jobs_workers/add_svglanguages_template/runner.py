"""
Runner module for add_svglanguages_template.
"""

from __future__ import annotations

import logging

from ...objects import JobsRunner
from .worker import AddSvgSVGLanguagesTemplate

logger = logging.getLogger(__name__)


def add_svglanguages_template_to_templates(data: JobsRunner) -> None:
    """
    Background worker
    """
    logger.info("Starting job %s: add {{SVGLanguages|...}} template to templates pages.", data.job_id)

    worker = AddSvgSVGLanguagesTemplate(data)
    worker.run()


__all__ = [
    "add_svglanguages_template_to_templates",
]
