"""
Worker module for copy_svg_langs.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict

from ...app_routes.utils.args_utils import parse_args, Args

from ...config import settings

from ...jobs_workers.base_worker import BaseJobWorker
from .job import CopySvgLangsProcessor

logger = logging.getLogger(__name__)


class CopySvgLangsWorker(BaseJobWorker):
    """
    Worker for copying SVG translations from a main file to its versions.
    """

    def __init__(
        self,
        task_id: int,
        title: str,
        args: Args,
        user: dict[str, Any] | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.title = title
        self.args = parse_args(args, settings.disable_uploads)  # Args
        super().__init__(task_id, user, cancel_event)

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "copy_svg_langs"

    def get_initial_result(self) -> dict[str, Any]:
        """Return the initial result structure."""
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "title": self.title,
            "stages": {
                "initialize": {"number": 1, "sub_name": "", "status": "Running", "message": "Starting workflow"},
                "text": {"sub_name": "", "number": 2, "status": "Pending", "message": "Getting text"},
                "titles": {"sub_name": "", "number": 3, "status": "Pending", "message": "Getting titles"},
                "translations": {"sub_name": "", "number": 4, "status": "Pending", "message": "Getting translations"},
                "download": {"sub_name": "", "number": 5, "status": "Pending", "message": "Downloading files"},
                "nested": {"sub_name": "", "number": 6, "status": "Pending", "message": "Analyze nested files"},
                "inject": {"sub_name": "", "number": 7, "status": "Pending", "message": "Injecting translations"},
                "upload": {"sub_name": "", "number": 8, "status": "Pending", "message": "Uploading files"},
            },
            "summary": {},
        }

    def process(self) -> dict[str, Any]:
        processor = CopySvgLangsProcessor(
            task_id=self.task_id,
            title=self.title,
            args=self.args,
            user=self.user,
            result=self.result,
            result_file=self.result_file,
            cancel_event=self.cancel_event,
        )
        return processor.run()


# --- main pipeline --------------------------------------------
def copy_svg_langs_worker_entry(
    task_id: str,
    title: str,
    args: Any,
    user: Dict[str, str] | None,
    *,
    cancel_event: threading.Event | None = None,
) -> None:
    """Entry point for the background job."""
    if not title or not args:
        logger.error(f"Job {task_id}: Missing title or args")
        return

    worker = CopySvgLangsWorker(
        task_id=task_id,
        title=title,
        args=args,
        user=user,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "copy_svg_langs_worker_entry",
    "CopySvgLangsWorker",
]
