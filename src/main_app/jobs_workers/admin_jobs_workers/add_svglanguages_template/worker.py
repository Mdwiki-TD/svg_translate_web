"""
Worker module for add_svglanguages_template.
"""

from __future__ import annotations

import logging

from mwclient.client import Site

from ....api_services import MwClientPage
from ....database.models import TemplateRecord
from ....database.services import TemplateService
from ...base_worker import BaseObjectsJobWorker
from ...objects import JobsRunner
from .objects import AddSvgLanguagesWorkerObject, OneStep, TemplateInfo
from .utils import RE_SVG_LANG, add_template_to_text, extract_svg_file_name

logger = logging.getLogger(__name__)


class AddSvgSVGLanguagesTemplate(BaseObjectsJobWorker):
    """
    Worker for add_svglanguages_template.
    Steps:
        1. load template wikitext
        2. generate SVGLanguages template text
        3. check if wikitext already has template {{SVGLanguages|...}} compare if text need to be updated
        4. add template {{SVGLanguages|...}} to wikitext
        5. save page with new wikitext
    """

    def __init__(self, data: JobsRunner) -> None:
        self.site: Site | None = None
        super().__init__(data)
        self.args = data.args or {}

        self.result: AddSvgLanguagesWorkerObject = AddSvgLanguagesWorkerObject(
            job_id=self.job_id,
            args=self.args,
        )

        self.limit_items = self.args.get("limit_items") or 0

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "add_svglanguages_template"

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _load_templates(self) -> list[TemplateRecord]:
        templates = TemplateService().list()
        templates = [t for t in templates if t.title.startswith("Template:OWID/")]
        return self._apply_limits(templates)

    def _apply_limits(self, templates: list[TemplateRecord]) -> list[TemplateRecord]:
        _limit = self.limit_items if isinstance(self.limit_items, int) else 0
        if _limit > 0 and len(templates) > _limit:
            logger.info("Job %s: limiting from %d to %d page", self.job_id, len(templates), _limit)
            return templates[:_limit]

        return templates

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------
    def _process_one_item(self, file_info: TemplateInfo) -> bool:

        page = MwClientPage(file_info.template_title, self.site)
        # Step 1 - load_template_text
        if not self._step_load_template_text(file_info, page):
            self.result.pages_failed.append(file_info.to_dict())
            return False

        match = RE_SVG_LANG.search(file_info._text if file_info._text else "")
        if match:
            file_info.steps.load_template_text = OneStep(
                result=None,
                msg="Skipped - page content is already has {{SVGLanguages|...}}",
            )
            self.result.pages_skipped.append(file_info.to_dict())
            return False

        # Step 2 generate_template_text
        if not self._step_generate_template_text(file_info):
            self.result.pages_failed.append(file_info.to_dict())
            return False

        # Step 3 add_template_text
        if not self._step_add_template(file_info):
            self.result.pages_skipped.append(file_info.to_dict())
            return False

        # Step 4 save_new_text
        if not self._step_save_new_text(file_info, page):
            self.result.pages_failed.append(file_info.to_dict())
            return False

        file_info.status = "completed"
        # self.result.pages_processed.append(file_info.to_dict())
        self.result.pages_success.append(file_info.to_dict())

        return True

    # ------------------------------------------------------------------
    # Individual pipeline steps
    # ------------------------------------------------------------------

    def _step_load_template_text(self, info: TemplateInfo, page: MwClientPage) -> bool:
        """Download the original Template wikitext. Returns True on success."""
        text = page.get_text()
        if not text:
            self._fail(info, "load_template_text", f"Could not retrieve text for {info.template_title}")
            return False

        info.steps.load_template_text = OneStep(result=True, msg="Loaded template text")
        info._text = text
        return True

    def _step_generate_template_text(self, info: TemplateInfo) -> bool:
        """ """
        translate_link_file_name = extract_svg_file_name(info._text)

        if not translate_link_file_name:
            self._fail(info, "generate_template_text", f"Could not load svgtranslate link for {info.template_title}")
            return False

        info.steps.generate_template_text = OneStep(result=True, msg="Template wikitext generated")

        info._template_text = f"{{{{SVGLanguages|{translate_link_file_name}}}}}"

        return True

    def _step_add_template(self, info: TemplateInfo) -> bool:
        """ """
        info._new_text = add_template_to_text(info._text, info._template_text)

        if info._text and (info._text.strip() == info._new_text.strip()):
            info.steps.add_template_text = OneStep(result=None, msg="Skipped - page content is already identical")
            info.status = "skipped"
            return False

        info.steps.add_template_text = OneStep(result=True, msg="Wikitext updated")
        return True

    def _step_save_new_text(self, info: TemplateInfo, page: MwClientPage) -> bool:
        """Create/Update the OWID gallery page on Commons. Returns True on success."""
        # Expected pattern: Template:OWID/... -> OWID/...

        update_result = page.edit(
            info._new_text,
            summary=f"Adding {info._template_text}",
        )

        if update_result["success"]:
            info.steps.save_new_text = OneStep(
                result=True,
                msg="Template page updated.",
                newrevid=update_result.get("newrevid", 0),
            )
            return True

        err = update_result.get("error", "Unknown error")
        self._fail(info, "save_new_text", err)
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fail(self, file_info: TemplateInfo, step: str, error: str) -> None:
        """Mark a step and the file as failed, and increment the summary counter."""
        setattr(file_info.steps, step, OneStep(result=False, msg=error))
        file_info.status = "failed"
        file_info.error = error

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def process(self) -> AddSvgLanguagesWorkerObject:

        if not self._check_site():
            return self.result

        templates = self._load_templates()
        self.result.summary.total = len(templates)
        logger.info("Job %s: Found %d templates", self.job_id, len(templates))

        per_item = self.get_priority(len(templates))

        for n, template in enumerate(templates, start=1):
            if self.is_cancelled():
                break

            logger.info("Job %s: Processing %d/%d: %s", self.job_id, n, len(templates), template.title)

            # file info
            file_info = TemplateInfo(
                template_id=template.id,
                template_title=template.title,
            )

            ok = self._process_one_item(file_info)
            self.update_status(file_info)

            if ok and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            if n == 1 or n % per_item == 0:
                self._save_progress()

        if self.result.status in ["pending", "running"]:
            self.result.status = "completed"

        self.result.summary.failed = len(self.result.pages_failed)
        self.result.summary.skipped = len(self.result.pages_skipped)
        self.result.summary.success = len(self.result.pages_success)

        return self.result

    def update_status(self, info: TemplateInfo) -> None:
        """
        TODO: move self.result.<stats>.append() into this method
        """
        self.result.summary.processed += 1
        if info.status.lower() in ["pending", "running"]:
            info.status = "completed"


__all__ = [
    "AddSvgSVGLanguagesTemplate",
]
