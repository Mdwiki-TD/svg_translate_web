"""
Processor class
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import mwclient
import requests

from ... import template_service
from ...api_services.clients import create_commons_session, get_user_site
from ...api_services.text_api import create_page, get_page_text
from ...config import settings
from ...db.db_Templates import TemplateRecord
from .. import jobs_service
from .owid_template_converter import create_new_text

logger = logging.getLogger(__name__)

StepResult = dict[str, Any]


@dataclass
class TemplateProcessingInfo:
    """Holds all state for a single template being processed."""

    template_id: int
    template_title: str
    new_page_title: str | None = None
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

    # Internal temporary state
    _template_text: str | None = None
    _new_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_title": self.template_title,
            "new_page_title": self.new_page_title,
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
            jobs_service.update_job_status(self.job_id, "running", self.result_file, job_type="create_owid_pages")
        except LookupError:
            logger.warning(
                f"Job {self.job_id}: Could not update status to running – " "job record might have been deleted."
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
        templates = [t for t in templates if t.title.startswith("Template:OWID/")]
        return self._apply_limits(templates)

    def _apply_limits(self, templates: list[TemplateRecord]) -> list[TemplateRecord]:
        upload_limit = int(settings.dynamic.get("create_owid_pages_limit", 0))
        if upload_limit > 0 and len(templates) > upload_limit:
            logger.info(
                f"Job {self.job_id}: create owid pages limit – "
                f"limiting from {len(templates)} to {upload_limit} files"
            )
            return templates[:upload_limit]

        return templates

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------

    def _process_template(self, template: TemplateRecord) -> None:
        file_info = TemplateProcessingInfo(
            template_id=template.id,
            template_title=template.title,
        )

        # Step 1 – load_template_text
        if not self._step_load_template_text(file_info):
            self._append(file_info)
            return

        # Step 2 – create_new_text
        if not self._step_create_new_text(file_info):
            self._append(file_info)
            return

        # Step 3 – create_new_page
        if not self._step_create_new_page(file_info):
            self._append(file_info)
            return

        file_info.status = "completed"
        self.result["summary"]["processed"] += 1
        self._append(file_info)

    # ------------------------------------------------------------------
    # Individual pipeline steps
    # ------------------------------------------------------------------

    def _step_load_template_text(self, info: TemplateProcessingInfo) -> bool:
        """Download the original Template wikitext. Returns True on success."""
        try:
            text = get_page_text(info.template_title, self.site)
            if not text:
                self._fail(info, "load_template_text", f"Could not retrieve text for {info.template_title}")
                return False

            info.steps["load_template_text"] = {"result": True, "msg": "Loaded template text"}
            info._template_text = text
            return True
        except Exception as exc:
            self._fail(info, "load_template_text", str(exc))
            return False

    def _step_create_new_text(self, info: TemplateProcessingInfo) -> bool:
        """Generate the new OWID page wikitext. Returns True on success."""
        try:
            new_text = create_new_text(info._template_text, info.template_title)
            info.steps["create_new_text"] = {"result": True, "msg": "Target wikitext generated"}
            info._new_text = new_text
            return True
        except Exception as exc:
            self._fail(info, "create_new_text", str(exc))
            return False

    def _step_create_new_page(self, info: TemplateProcessingInfo) -> bool:
        """Create/Update the OWID gallery page on Commons. Returns True on success."""
        # Expected pattern: Template:OWID/... -> OWID/...
        new_title = info.template_title.replace("Template:OWID/", "OWID/")
        try:
            res = create_page(
                new_title, info._new_text, self.site, summary=f"Creating OWID page from [[{info.template_title}]]"
            )

            if not res["success"]:
                err = res.get("error", "Unknown error")
                self._fail(info, "create_new_page", err)
                return False

            self.result["summary"]["created"] += 1
            info.steps["create_new_page"] = {"result": True, "msg": f"Created/Updated page: {new_title}"}
            info.new_page_title = new_title
            return True
        except Exception as exc:
            self._fail(info, "create_new_page", str(exc))
            return False

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
        if self.result.get("status") not in ("cancelled", "failed"):
            self.result["status"] = "completed"
            self.result["completed_at"] = datetime.now().isoformat()
            logger.info(f"Job {self.job_id}: OWID pages creation completed")

    def _append(self, file_info: TemplateProcessingInfo) -> None:
        self.result["templates_processed"].append(file_info.to_dict())


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
