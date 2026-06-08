"""
Worker module for add_svglanguages_template.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

import mwclient

from ....api_services.clients import get_user_site
from ....api_services.pages_api import get_page_text, update_page_text
from ....db.models import TemplateRecord
from ....db.services import list_templates
from ...base_worker import BaseJobWorker
from .utils import RE_SVG_LANG, add_template_to_text, load_link_file_name

logger = logging.getLogger(__name__)
StepResult = dict[str, Any]


@dataclass
class TemplateInfo:
    """Holds all state for a single template being processed."""

    template_id: int
    template_title: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    error: str | None = None
    steps: dict[str, StepResult] = field(
        default_factory=lambda: {
            "load_template_text": {"result": None, "msg": ""},
            "generate_template_text": {"result": None, "msg": ""},
            "add_template_text": {"result": None, "msg": ""},
            "save_new_text": {"result": None, "msg": ""},
        }
    )

    # Internal temporary state
    _text: str | None = None
    _template_text: str | None = None
    _new_text: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_title": self.template_title,
            "timestamp": self.timestamp,
            "status": self.status,
            "error": self.error,
            "steps": self.steps,
        }


class AddSvgSVGLanguagesTemplate(BaseJobWorker):
    """
    Worker for add_svglanguages_template.
    Steps:
        1. load template wikitext
        2. generate SVGLanguages template text
        3. check if wikitext already has template {{SVGLanguages|...}} compare if text need to be updated
        4. add template {{SVGLanguages|...}} to wikitext
        5. save page with new wikitext
    """

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.job_id = job_id
        self.user = user
        self.cancel_event = cancel_event
        self.site: mwclient.Site | None = None
        self.limit_items = args.get("limit_items") if args else 0
        self.args = args or {}

        super().__init__(job_id, user, cancel_event)
        self.result: Dict[str, Any] = self.get_initial_result()

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "add_svglanguages_template"

    def get_initial_result(self) -> Dict[str, Any]:
        """Return the initial result structure."""
        return {
            "status": "pending",
            "errors": [{"error": "", "error_type": ""}],
            "args": {},
            "job_id": self.job_id,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "total": 0,
                "processed": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
            },
            "pages_processed": [],
            "pages_success": [],
            "pages_skipped": [],
            "pages_failed": [],
        }

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _load_templates(self) -> list[TemplateRecord]:
        templates = list_templates()
        templates = [t for t in templates if t.title.startswith("Template:OWID/")]
        return self._apply_limits(templates)

    def _apply_limits(self, templates: list[TemplateRecord]) -> list[TemplateRecord]:
        _limit = self.limit_items if isinstance(self.limit_items, int) else 0
        if _limit > 0 and len(templates) > _limit:
            logger.info(f"Job {self.job_id}: limiting from {len(templates)} to {_limit} page")
            return templates[:_limit]

        return templates

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------
    def _process_template(self, template: TemplateRecord) -> bool:
        self.result["summary"]["processed"] += 1

        # file info
        file_info = TemplateInfo(
            template_id=template.id,
            template_title=template.title,
        )

        # Step 1 - load_template_text
        if not self._step_load_template_text(file_info):
            self._append(file_info, key="pages_failed")
            return False

        match = RE_SVG_LANG.search(file_info._text if file_info._text else "")
        if match:
            self._skip_step(
                file_info, "load_template_text", "Skipped - page content is already has {{SVGLanguages|...}}"
            )
            self._append(file_info, key="pages_skipped")
            return False

        # Step 2 generate_template_text
        if not self._step_generate_template_text(file_info):
            self._append(file_info, key="pages_failed")
            return False

        # Step 3 add_template_text
        if not self._step_add_template(file_info):
            self._append(file_info, key="pages_skipped")
            return False

        # Step 4 save_new_text
        if not self._step_save_new_text(file_info):
            self._append(file_info, key="pages_failed")
            return False

        file_info.status = "completed"
        # self._append(file_info, key="pages_processed")
        self._append(file_info, key="pages_success")

        return True

    # ------------------------------------------------------------------
    # Individual pipeline steps
    # ------------------------------------------------------------------

    def _step_load_template_text(self, info: TemplateInfo) -> bool:
        """Download the original Template wikitext. Returns True on success."""
        text = get_page_text(info.template_title, self.site)
        if not text:
            self._fail(info, "load_template_text", f"Could not retrieve text for {info.template_title}")
            return False

        info.steps["load_template_text"] = {"result": True, "msg": "Loaded template text"}
        info._text = text
        return True

    def _step_generate_template_text(self, info: TemplateInfo) -> bool:
        """ """
        translate_link_file_name = load_link_file_name(info._text)

        if not translate_link_file_name:
            self._fail(info, "generate_template_text", f"Could not load svgtranslate link for {info.template_title}")
            return False

        info.steps["generate_template_text"] = {"result": True, "msg": "Template wikitext generated"}

        info._template_text = f"{{{{SVGLanguages|{translate_link_file_name}}}}}"

        return True

    def _step_add_template(self, info: TemplateInfo) -> bool:
        """ """
        info._new_text = add_template_to_text(info._text, info._template_text)

        if info._text.strip() == info._new_text.strip():
            self._skip_step(info, "add_template_text", "Skipped - page content is already identical")
            info.status = "skipped"
            return False

        info.steps["add_template_text"] = {"result": True, "msg": "Wikitext updated"}
        return True

    def _step_save_new_text(self, info: TemplateInfo) -> bool:
        """Create/Update the OWID gallery page on Commons. Returns True on success."""
        # Expected pattern: Template:OWID/... -> OWID/...
        update_result = update_page_text(
            info.template_title,
            info._new_text,
            self.site,
            summary=f"Adding {info._template_text}",
        )

        if update_result["success"]:
            info.steps["save_new_text"] = {"result": True, "msg": "Template page updated."}
            return True

        err = update_result.get("error", "Unknown error")
        self._fail(info, "save_new_text", err)
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fail(self, file_info: TemplateInfo, step: str, error: str) -> None:
        """Mark a step and the file as failed, and increment the summary counter."""
        file_info.steps[step] = {"result": False, "msg": error}
        file_info.status = "failed"
        file_info.error = error

    def _skip_step(self, file_info: TemplateInfo, step: str, reason: str) -> None:
        """Mark a step as skipped (result=None)."""
        file_info.steps[step] = {"result": None, "msg": reason}

    def _append(self, file_info: TemplateInfo, key: str = "pages_processed") -> None:
        self.result[key].append(file_info.to_dict())

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def process(self) -> Dict[str, Any]:
        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.log_no_site_error()
            return self.result

        templates = self._load_templates()
        self.result["summary"]["total"] = len(templates)
        logger.info(f"Job {self.job_id}: Found {len(templates)} templates")

        per_item = self.get_priority(len(templates))

        for n, template in enumerate(templates, start=1):
            if self.is_cancelled():
                break

            logger.info(f"Job {self.job_id}: Processing {n}/{len(templates)}: {template.title}")
            ok = self._process_template(template)

            if ok and self.check_cancel_db_periodic():
                logger.info(f"Job {self.job_id}: Cancelled due to periodic check")
                break

            if n == 1 or n % per_item == 0:
                self._save_progress()

        if self.result.get("status") in ["pending", "running"]:
            self.result["status"] = "completed"

        self.result["summary"]["failed"] = len(self.result["pages_failed"])
        self.result["summary"]["skipped"] = len(self.result["pages_skipped"])
        self.result["summary"]["success"] = len(self.result["pages_success"])

        return self.result


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
    logger.info(f"Starting job {job_id}: add {{{{SVGLanguages|...}}}} template to templates pages.")

    if args and args.get("add_svglanguages_limit_items"):
        args.update({"limit_items": args.get("add_svglanguages_limit_items")})

    worker = AddSvgSVGLanguagesTemplate(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "add_svglanguages_template_to_templates",
    "AddSvgSVGLanguagesTemplate",
]
