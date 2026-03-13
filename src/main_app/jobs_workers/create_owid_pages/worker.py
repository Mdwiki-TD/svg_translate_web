"""
Worker module for create_owid_pages.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

import mwclient

from ... import template_service
from ...api_services.clients import get_user_site
from ...api_services.pages_api import create_page, is_page_exists
from ...api_services.text_api import get_page_text
from ...config import settings
from ...db.db_Templates import TemplateRecord
from ..base_worker import BaseJobWorker
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


class CreateOwidPagesWorker(BaseJobWorker):
    """
    Worker for create_owid_pages.
    Steps:
        1. load template wikitext
        2. create new wikitext using create_new_text
        3. check if new page already exists then compare if text need to be updated
        4. create new page with new wikitext
    """

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any] | None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self.job_id = job_id
        self.user = user
        self.cancel_event = cancel_event
        self.site: mwclient.Site | None = None

        self.result = {}

        super().__init__(job_id, user, cancel_event)

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _load_templates(self) -> list[TemplateRecord]:
        templates = template_service.list_templates()
        templates = [t for t in templates if t.title.startswith("Template:OWID/")]
        return self._apply_limits(templates)

    def _apply_limits(self, templates: list[TemplateRecord]) -> list[TemplateRecord]:
        _limit = int(settings.dynamic.get("create_owid_pages_limit", 0))
        if _limit > 0 and len(templates) > _limit:
            logger.info(
                f"Job {self.job_id}: create owid pages limit – " f"limiting from {len(templates)} to {_limit} page"
            )
            return templates[:_limit]

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

        # Step 3 – check if new page already exists then compare if text need to be updated
        # if page text == new text then summary.skipped++ else summary.updated++
        if not self._step_check_exists_and_update(file_info):
            self._append(file_info)
            return

        # Step 4 – create_new_page
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
        text = get_page_text(info.template_title, self.site)
        if not text:
            self._fail(info, "load_template_text", f"Could not retrieve text for {info.template_title}")
            return False

        info.steps["load_template_text"] = {"result": True, "msg": "Loaded template text"}
        info._template_text = text
        return True

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

    def _step_check_exists_and_update(self, info: TemplateProcessingInfo) -> bool:
        """
        Check if the target OWID page exists and compare its content.
        If identical, skip creation. If different, update here and return False.
        Returns True to continue to Step 4 (Creation) if page does not exist.
        """
        new_title = self.create_new_page_title(info)

        if not is_page_exists(new_title, self.site):
            return True

        # Page exists, check if update is needed
        current_text = get_page_text(new_title, self.site)
        if current_text.strip() == info._new_text.strip():
            self._skip_step(info, "create_new_page", "Skipped – page content is already identical")
            info.status = "skipped"
            info.new_page_title = new_title
            self.result["summary"]["skipped"] += 1
            self.result["summary"]["processed"] += 1
            return False

        # Content is different, perform update
        res = create_page(
            new_title,
            info._new_text,
            self.site,
            summary=f"Updating OWID page from [[{info.template_title}]]",
        )

        if not res["success"]:
            err = res.get("error", "Unknown error")
            self._fail(info, "create_new_page", err)
            return False

        self.result["summary"]["updated"] += 1
        self.result["summary"]["processed"] += 1
        info.steps["create_new_page"] = {"result": True, "msg": f"Updated page: {new_title}"}
        info.new_page_title = new_title
        info.status = "completed"
        return False

    def _step_create_new_page(self, info: TemplateProcessingInfo) -> bool:
        """Create/Update the OWID gallery page on Commons. Returns True on success."""
        # Expected pattern: Template:OWID/... -> OWID/...
        new_title = self.create_new_page_title(info)

        res = create_page(
            new_title,
            info._new_text,
            self.site,
            summary=f"Creating OWID page from [[{info.template_title}]]",
        )

        if not res["success"]:
            err = res.get("error", "Unknown error")
            self._fail(info, "create_new_page", err)
            return False

        self.result["summary"]["created"] += 1
        info.steps["create_new_page"] = {"result": True, "msg": f"Created/Updated page: {new_title}"}
        info.new_page_title = new_title
        return True

    def create_new_page_title(self, info):
        new_title = info.template_title.replace("Template:OWID/", "OWID/")
        if new_title == info.template_title:
            new_title = "OWID/" + info.template_title.removeprefix("Template:")
        return new_title

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

    def _append(self, file_info: TemplateProcessingInfo) -> None:
        self.result["templates_processed"].append(file_info.to_dict())

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "create_owid_pages"

    def get_initial_result(self) -> Dict[str, Any]:
        """Return the initial result structure."""
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "total": 0,
                "processed": 0,
                "created": 0,
                "updated": 0,
                "failed": 0,
                "skipped": 0,
            },
            "templates_processed": [],
        }

    def process(self):

        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.result["status"] = "failed"
            self.result["failed_at"] = datetime.now().isoformat()
            return self.result

        templates = self._load_templates()
        self.result["summary"]["total"] = len(templates)
        logger.info(f"Job {self.job_id}: Found {len(templates)} templates with main files")

        for n, template in enumerate(templates, start=1):
            if self.is_cancelled():
                break

            logger.info(f"Job {self.job_id}: Processing {n}/{len(templates)}: {template.title}")
            self._process_template(template)

            if n == 1 or n % 10 == 0:
                self._save_progress()

        self.result["status"] = "completed"
        return self.result


def create_owid_pages_for_templates(
    job_id: int,
    user: Dict[str, Any] | None = None,
    cancel_event: threading.Event | None = None,
) -> None:
    """
    Background worker
    """
    logger.info(f"Starting job {job_id}: collect main files for templates")
    worker = CreateOwidPagesWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
    )
    worker.run()


__all__ = [
    "create_owid_pages_for_templates",
    "CreateOwidPagesWorker",
]
