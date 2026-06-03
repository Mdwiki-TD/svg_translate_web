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
        job_id: int,
        args: Any,
        user: dict[str, Any] | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.job_id = job_id
        self.args = args
        self.upload_limit = args.get("upload_limit") if args else 0

        super().__init__(job_id, user, cancel_event)

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
            job_id=self.job_id,
            args=self.args,
            user=self.user,
            result=self.result,
            result_file=self.result_file,
            cancel_event=self.cancel_event,
            upload_limit=self.upload_limit,
        )
        return processor.run()


# --- main pipeline --------------------------------------------
def copy_svg_langs_worker_entry(
    *,
    job_id: str,
    user: Dict[str, str] | None,
    cancel_event: threading.Event | None = None,
    args: Dict[str, Any] | None = None,
) -> None:
    """Entry point for the background job."""

    if args and args.get("copy_svg_langs_upload_limit"):
        args.update({"upload_limit": args.get("copy_svg_langs_upload_limit")})

    worker = CopySvgLangsWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "copy_svg_langs_worker_entry",
    "CopySvgLangsWorker",
]
