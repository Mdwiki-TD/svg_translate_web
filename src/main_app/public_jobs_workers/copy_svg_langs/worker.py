"""
Worker module for copy_svg_langs.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any, Dict

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
        args: Any,
        user: dict[str, Any] | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.task_id = task_id
        self.args = args
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
            "title": None,
            "stages": {
                "text": {"status": "Pending", "message": "Getting text"},
                "titles": {"status": "Pending", "message": "Getting titles"},
                "translations": {"status": "Pending", "message": "Getting translations"},
                "download": {"status": "Pending", "message": "Downloading files"},
                "nested": {"status": "Pending", "message": "Analyze nested files"},
                "inject": {"status": "Pending", "message": "Injecting translations"},
                "upload": {"status": "Pending", "message": "Uploading files"},
            },
            "summary": {},
            "results_summary": {},
            "files_processed": {},
        }

    def process(self) -> dict[str, Any]:
        processor = CopySvgLangsProcessor(
            task_id=self.task_id,
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
    args: Any,
    user: Dict[str, str] | None,
    *,
    cancel_event: threading.Event | None = None,
) -> None:
    """Entry point for the background job."""
    worker = CopySvgLangsWorker(
        task_id=task_id,
        args=args,
        user=user,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "copy_svg_langs_worker_entry",
    "CopySvgLangsWorker",
]
