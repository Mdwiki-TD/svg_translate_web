"""
Processor class
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import mwclient
import requests

from ... import template_service
from ...config import settings
from ...db.db_Templates import TemplateRecord
from ...api_services.clients import create_commons_session
from ...api_services.text_api import get_page_text, update_page_text, create_page
from ...api_services.clients import get_user_site
from .. import jobs_service

from .owid_template_converter import create_new_text

logger = logging.getLogger(__name__)

StepResult = dict[str, Any]


@dataclass
class TemplateProcessingInfo:
    """Holds all state for a single template being processed."""

    template_id: int
    template_title: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    error: str | None = None
    steps: dict[str, StepResult] = field(
        default_factory=lambda: {
            "load_template_text": {"result": None, "msg": ""},
            "create_new_text": {"result": None, "msg": ""},
            "create_new_page": {"result": None, "msg": ""},
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_title": self.template_title,
            "timestamp": self.timestamp,
            "status": self.status,
            "error": self.error,
            "steps": self.steps,
        }


class TemplateProcessor:
    """
    Orchestrates the full pipeline for cropping SVG files and uploading them to Commons.
    Steps:
        2. load template wikitext
        3. create new wikitext using create_new_text
        4. create new page with new wikitext
    """

    def __init__(
        self,
        job_id: int,
        result: dict[str, Any],
        result_file: str,
        user: dict[str, Any] | None,
        *,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.job_id = job_id
        self.result = result
        self.result_file = result_file
        self.user = user
        self.cancel_event = cancel_event

        self.site: mwclient.Site | None = None
        self.session: requests.Session | None = None

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def run(self) -> dict[str, Any]:
        """Run the full crop pipeline and return the populated result dict."""
        if not self._initialize():
            return self.result

        templates = self._load_templates()
        self.result["summary"]["total"] = len(templates)
        logger.info(f"Job {self.job_id}: Found {len(templates)} templates with main files")

        for n, template in enumerate(templates, start=1):
            if self._is_cancelled():
                break

            if n == 1 or n % 10 == 0:
                try:
                    jobs_service.save_job_result_by_name(self.result_file, self.result)
                except Exception as exc:
                    logger.warning(
                        f"Job {self.job_id}: Failed to persist periodic progress; continuing",
                        exc_info=exc,
                    )
            logger.info(f"Job {self.job_id}: Processing {n}/{len(templates)}: {template.title}")
            self._process_template(template)

        self._finalize()
        return self.result

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _initialize(self) -> bool:
        """Set up job status, auth session, and site. Returns False on failure."""
        try:
            jobs_service.update_job_status(
                self.job_id,
                "running",
                self.result_file,
                job_type="create_owid_pages"
            )
        except LookupError:
            logger.warning(
                f"Job {self.job_id}: Could not update status to running – "
                "job record might have been deleted."
            )
            return False

        self.session = create_commons_session(settings.oauth.user_agent)
        self.site = get_user_site(self.user)

        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result["status"] = "failed"
            self.result["failed_at"] = datetime.now().isoformat()
            return False

        return True

    def _load_templates(self) -> list[TemplateRecord]:
        templates = template_service.list_templates()
        return templates

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------

    def _process_template(self, template: TemplateRecord) -> None:
        file_info = TemplateProcessingInfo(
            template_id=template.id,
            template_title=template.title,
            original_file=template.last_world_file,
        )

        # Step 1 – load_template_text

        # Step 2 – create_new_text

        # Step 3 – create_new_page

        self._append(file_info)

    # ------------------------------------------------------------------
    # Individual pipeline steps
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fail(self, file_info: TemplateProcessingInfo, step: str, error: str) -> None:
        """Mark a step and the file as failed, and increment the summary counter."""
        file_info.steps[step] = {"result": False, "msg": error}
        file_info.status = "failed"
        file_info.error = error
        self.result["summary"]["failed"] += 1

    def _skip_step(self, file_info: TemplateProcessingInfo, step: str, reason: str) -> None:
        """Mark a step as skipped (result=None)."""
        file_info.steps[step] = {"result": None, "msg": reason}

    def _skip_upload_steps(self, file_info: TemplateProcessingInfo) -> None:
        for step in ("upload_cropped", "update_original", "update_template"):
            self._skip_step(file_info, step, "Skipped – upload disabled")
        file_info.status = "skipped"
        self.result["summary"]["skipped"] += 1
        logger.info(f"Job {self.job_id}: Skipped upload for {file_info.cropped_filename} (upload disabled)")
        file_info.cropped_filename = None

    def _is_cancelled(self) -> bool:
        if self.cancel_event and self.cancel_event.is_set():
            logger.info(f"Job {self.job_id}: Cancellation detected, stopping.")
            self.result["status"] = "cancelled"
            self.result["cancelled_at"] = datetime.now().isoformat()
            return True
        return False

    def _finalize(self) -> None:
        # Mark as completed if not cancelled or failed
        if self.result.get("status") != "cancelled":
            self.result["status"] = "completed"
            logger.info(f"Job {self.job_id}: Crop processing completed")


# ------------------------------------------------------------------
# Backwards-compatible entry-point
# ------------------------------------------------------------------

def process_create_owid_pages(
    job_id: int,
    result: dict[str, Any],
    result_file: str,
    user: dict[str, Any] | None,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    """Thin shim kept for backwards compatibility."""
    processor = TemplateProcessor(
        job_id=job_id,
        result=result,
        result_file=result_file,
        user=user,
        cancel_event=cancel_event,
    )
    return processor.run()


__all__ = [
    "TemplateProcessor",
    "process_create_owid_pages",
]
