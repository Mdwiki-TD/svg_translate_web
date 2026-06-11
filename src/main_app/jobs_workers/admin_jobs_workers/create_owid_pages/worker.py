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
from mwclient.client import Site

from ....api_services import MwClientPage, get_user_site, is_pages_exists
from ....data import get_slug_categories
from ....db.models import TemplateRecord
from ....db.services import list_templates
from ....utils.wikitext import merge_categories, sort_categories
from ...base_worker import BaseJobWorker
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
            "update_text": {"result": None, "msg": ""},
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
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.update_all = False
        self.job_id = job_id
        self.user = user
        self.site: Site | None = None
        self.args = args or {}
        self.limit_items = args.get("limit_items") if args else 0
        if args and str(args.get("update_all", "")).lower() == "true":
            self.update_all = True

        super().__init__(job_id, user, cancel_event)
        self.result: Dict[str, Any] = self.get_initial_result()

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "create_owid_pages"

    def get_initial_result(self) -> Dict[str, Any]:
        """Return the initial result structure."""
        return {
            "note": "",
            "status": "pending",
            "errors": [],
            "args": {},
            "job_id": self.job_id,
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
            "pages_processed": [],
            "pages_created": [],
            "pages_updated": [],
            "pages_skipped": [],
            "pages_failed": [],
        }

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def process(self) -> Dict[str, Any]:
        self.result["args"].update({"update_all": str(self.update_all)})

        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self.log_no_site_error()
            return self.result

        templates = self._load_templates()
        len_all = len(templates)
        self.result["summary"]["total"] = len_all
        self._save_progress()

        if not self.update_all:
            templates = self.filter_created(templates)
            if not templates:
                self.result["summary"]["skipped"] = len_all
                self.result["status"] = "skipped"
                self.result["note"] = f"Nothing to create, All {len_all:,} pages already exist"
                logger.warning(f"Job {self.job_id}: No templates to process")
                return self.result

        # self.result["summary"]["total"] = len(templates)
        logger.info(f"Job {self.job_id}: Found {len(templates)} templates.")

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

        return self.result

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def filter_created(self, templates) -> list[TemplateRecord]:
        owid_pages = [t.title.removeprefix("Template:") for t in templates]
        pages_created = is_pages_exists(owid_pages, self.site)
        already_created = [x for x, v in pages_created.items() if v is True]

        if not already_created:
            logger.warning("filter_created failed returning all templates")
            return templates

        logger.debug(f"len of OWID already created pages: {len(already_created):,}")

        templates = [t for t in templates if t.title.removeprefix("Template:") not in already_created]
        logger.debug(f"len of templates after filter created pages: {len(templates):,}")

        return templates

    def _load_templates(self) -> list[TemplateRecord]:
        templates = list_templates()
        _templates = [t for t in templates if t.title.startswith("Template:OWID/")]
        return self._apply_limits(_templates)

    def _apply_limits(self, templates: list[TemplateRecord]) -> list[TemplateRecord]:
        _limit = self.limit_items if isinstance(self.limit_items, int) else 0
        if _limit > 0 and len(templates) > _limit:
            logger.info(f"Job {self.job_id}: limiting from {len(templates)} to {_limit} item")
            return templates[:_limit]

        return templates

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------
    def add_slug_categories(self, new_text: str, categories: list[str]) -> str:
        for x in categories:
            if x not in new_text:
                new_text += f"\n[[{x}]]"

        return new_text

    def _process_template(self, template: TemplateRecord) -> bool:
        self.result["summary"]["processed"] += 1

        # file info
        file_info = TemplateProcessingInfo(
            template_id=template.id,
            template_title=template.title,
        )

        # ----------------------------------
        # Step 1 - load_template_text
        if not self._step_load_template_text(file_info):
            self._append(file_info, key="pages_failed")
            return False

        # ----------------------------------
        # Step 2 - create_new_text
        if not self._step_create_new_text(file_info):
            self._append(file_info, key="pages_failed")
            return False

        if file_info._new_text and template.slug:
            categories = get_slug_categories(template.slug)
            file_info._new_text = self.add_slug_categories(file_info._new_text, categories)

        # ----------------------------------
        # Step 2 A) - check if new page already exists
        new_title = self.create_new_page_title(file_info)

        page = MwClientPage(new_title, self.site)

        if page.exists():
            # ----------------------------------
            # Step 3 - compare if text need to be updated
            upd_step = self._step_update(file_info, new_title)
            if upd_step is False:
                self._append(file_info, key="pages_failed")
            elif upd_step is None:
                self._append(file_info, key="pages_skipped")
            else:
                self._append(file_info, key="pages_updated")

            return upd_step is True

        # Step 4 - create_new_page
        create_step = self._step_create_new_page(file_info)
        if create_step is False:
            self._append(file_info, key="pages_failed")
            return False
        elif create_step is True:
            self._append(file_info, key="pages_created")
            return True

        # dead code?
        file_info.status = "completed"
        self._append(file_info, key="pages_processed")
        return True

    # ------------------------------------------------------------------
    # Individual pipeline steps
    # ------------------------------------------------------------------

    def _step_load_template_text(self, info: TemplateProcessingInfo) -> bool:
        """Download the original Template wikitext. Returns True on success."""
        text = MwClientPage(info.template_title, self.site).get_text()
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

    def _step_update(self, info: TemplateProcessingInfo, new_title: str) -> bool | None:
        """
        compare the target OWID page content.
        If identical, skip creation. If different, update here and return False.
        Returns True to continue to Step 4 (Creation) if page does not exist.
        """
        # Page exists, check if update is needed
        new_title_page = MwClientPage(new_title, self.site)

        current_text = new_title_page.get_text()
        if not current_text:
            self._fail(info, "update_text", f"Could not retrieve text for {new_title}")
            return False

        # extend categories from current text
        info._new_text = merge_categories(current_text, info._new_text)
        info._new_text = sort_categories(info._new_text)

        # sort current_text categories to compare with new text
        current_text = sort_categories(current_text)

        if current_text.strip() == info._new_text.strip():
            self._skip_step(info, "update_text", "Skipped - page content is already identical")
            info.status = "skipped"
            info.new_page_title = new_title
            self.result["summary"]["skipped"] += 1
            return None  # nothing to update

        # Content is different, perform update
        res = new_title_page.edit(
            info._new_text,
            f"Updating OWID page from [[{info.template_title}]]",
        )

        if res["success"]:
            self.result["summary"]["updated"] += 1
            info.steps["update_text"] = {
                "result": True,
                "msg": f"Updated page: {new_title}",
                "newrevid": res.get("newrevid", 0),
            }
            info.new_page_title = new_title
            info.status = "updated"
            return True

        err = res.get("error", "Unknown error")
        self._fail(info, "update_text", err)
        return False

    def _step_create_new_page(self, info: TemplateProcessingInfo) -> bool:
        """Create/Update the OWID gallery page on Commons. Returns True on success."""
        # Expected pattern: Template:OWID/... -> OWID/...
        new_title = self.create_new_page_title(info)

        new_title_page = MwClientPage(new_title, self.site)

        res = new_title_page.create(
            info._new_text,
            summary=f"Creating OWID page from [[{info.template_title}]]",
        )

        if not res["success"]:
            err = res.get("error", "Unknown error")
            self._fail(info, "create_new_page", err)
            return False

        self.result["summary"]["created"] += 1
        info.steps["create_new_page"] = {
            "result": True,
            "msg": f"Created: {new_title}",
            "newrevid": res.get("newrevid", 0),
        }
        info.new_page_title = new_title
        info.status = "created"
        return True

    def create_new_page_title(self, info: TemplateProcessingInfo) -> str:
        if info.template_title.startswith("Template:OWID/"):
            return info.template_title.replace("Template:OWID/", "OWID/", 1)

        return "OWID/" + info.template_title.removeprefix("Template:")

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

    def _append(self, file_info: TemplateProcessingInfo, key: str = "pages_processed") -> None:
        self.result[key].append(file_info.to_dict())


def create_owid_pages_for_templates(
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
    logger.info(f"Starting job {job_id}: create OWID pages for templates")

    if args and args.get("create_owid_pages_limit"):
        args.update({"limit_items": args.get("create_owid_pages_limit")})

    worker = CreateOwidPagesWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "create_owid_pages_for_templates",
    "CreateOwidPagesWorker",
]
