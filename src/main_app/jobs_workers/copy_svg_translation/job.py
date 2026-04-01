"""
Processor for copy_svg_translation
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any

import mwclient

from ...api_services.clients import get_user_site

logger = logging.getLogger(__name__)
StepResult = dict[str, Any]


class CopySvgTranslationProcessor:
    """
    Worker for copy_svg_translation.
    Steps:
        1.
        2.
        3.
        4.
        5.
    """

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any] | None,
        title: str | None,
        args: dict[str, Any] | None,
        result: dict[str, Any],
        result_file: str | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.job_id = job_id
        self.user = user
        self.args = args
        self.title = title

        self.cancel_event = cancel_event
        self.site: mwclient.Site | None = None

        self.result = {}

    def run(self):

        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result["status"] = "failed"
            self.result["failed_at"] = datetime.now().isoformat()
            return self.result

        # start steps

        return self.result


__all__ = [
    "CopySvgTranslationProcessor",
]
