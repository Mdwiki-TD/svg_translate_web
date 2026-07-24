"""
Worker module for cropping main files and uploading them with (cropped) suffix.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from mwclient.client import Site

from ....api_services import MwClientPage, create_commons_session, is_pages_exists
from ....config import settings
from ....db.models import TemplateRecord
from ....db.services import TemplateService
from ....utils.wikitext import (
    create_cropped_file_text,
    ensure_file_prefix,
    update_original_file_text,
    update_template_page_file_reference,
)
from ...base_worker import BaseObjectsJobWorker
from .objects import CropFileProcessingInfo, CropMainFilesWorkerObject
from .steps.crop_file import crop_svg_file
from .steps.crop_utils import generate_cropped_filename
from .steps.download import download_file_for_cropping
from .steps.upload import upload_cropped_file

logger = logging.getLogger(__name__)


class CropMainFilesWorker(BaseObjectsJobWorker):
    """
    Orchestrates the full pipeline for cropping SVG files and uploading them to Commons.

    Pipeline steps per file:
        1. Download  - fetch the original file from Commons
        2. Crop      - crop the SVG to its bounding-box
        3. Upload    - upload the cropped version under a new filename
        4. Update original  - add a link to the cropped file in the original file's wikitext
        5. Update template  - point the template page at the cropped file
        6. Update page      - point the content page at the cropped file
    """

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.site: Site | None = None

        super().__init__(job_id, user, cancel_event)
        self.result: CropMainFilesWorkerObject = CropMainFilesWorkerObject()
        self.args = args or {}
        self.upload_files = bool(self.args.get("upload_files"))
        self.result.args = self.args
        self.upload_limit = self.args.get("upload_limit") or 0

        self.exists: dict[str, Any] = {}
        self.original_dir = Path(settings.paths.crop_main_files_path) / "original"
        self.cropped_dir = Path(settings.paths.crop_main_files_path) / "cropped"

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "crop_main_files"

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def process(self) -> CropMainFilesWorkerObject:
        """Execute the full pipeline."""

        if not self._check_site():
            return self.result

        templates = self._load_templates()

        self.result.summary.total = len(templates)
        logger.info("Job %s: Found %d templates with main files", self.job_id, len(templates))

        self._check_exists(templates)

        per_item = self.get_priority(len(templates))

        for n, template in enumerate(templates, start=1):
            if self.is_cancelled():
                break

            logger.info("Job %s: Processing %d/%d: %s", self.job_id, n, len(templates), template.title)
            ok = self._process_one_item(template)

            if ok and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            if n == 1 or n % per_item == 0:
                self._save_progress()

        if self.result.status in ["pending", "running"]:
            self.result.status = "completed"

        return self.result

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _check_exists(self, templates) -> None:
        cropped_filenames = [generate_cropped_filename(template.last_world_file) for template in templates]
        exists_files = is_pages_exists(cropped_filenames, self.site)

        for file in exists_files:
            self.exists[file.removeprefix("File:")] = exists_files[file]

        logger.info("self.exists: %d", len(self.exists))

    def _load_templates(self) -> list[TemplateRecord]:
        templates = TemplateService().list_templates()
        _templates = [t for t in templates if t.last_world_file]
        return self._apply_limits(_templates)

    def _apply_limits(self, templates: list[TemplateRecord]) -> list[TemplateRecord]:
        _limit = self.upload_limit if isinstance(self.upload_limit, int) else 0
        if _limit > 0 and len(templates) > _limit:
            logger.info("Job %s: limiting from %d to %d item", self.job_id, len(templates), _limit)
            return templates[:_limit]

        return templates

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------
    def _process_one_item(self, template: TemplateRecord) -> bool:
        self.result.summary.processed += 1

        cropped_filename = generate_cropped_filename(template.last_world_file)

        # file info
        file_info = CropFileProcessingInfo(
            template_id=template.id,
            template_title=template.title,
            original_file=template.last_world_file,
            cropped_filename=cropped_filename,
            timestamp=datetime.now().isoformat(),
        )

        # pre steps if the file already in commons, skip download/upload files.
        if self._check_file_exists(cropped_filename):
            self._skip_process(file_info)
            # Step 4 & 5 - Update wikitext references
            updated = self.update_file_references(file_info)

            if updated:
                file_info.status = "completed"
                self.result.summary.updated += 1
                self.result.pages_updated.append(file_info.to_dict())
                return True
            else:
                # if all file_info.steps "result" is None do:
                if all(step["result"] is None for step in file_info.steps.values()):
                    file_info.status = "skipped"
                    self.result.summary.skipped += 1

            self.result.pages_skipped.append(file_info.to_dict())
            return False

        # ----------------------------------
        # Step 1 - Download
        if not self._step_download(file_info, template):
            self.result.pages_failed.append(file_info.to_dict())
            return False

        # ----------------------------------
        # Step 2 - Crop
        cropped_output_path = self.cropped_dir / Path(cropped_filename.removeprefix("File:")).name
        if not self._step_crop(file_info, template, cropped_output_path):
            self.result.pages_failed.append(file_info.to_dict())
            return False

        # Upload disabled → mark skipped and move on
        if not self.upload_files:
            self._skip_upload_steps(file_info)
            self.result.pages_skipped.append(file_info.to_dict())
            return False

        # ----------------------------------
        # Step 3 - Upload cropped file
        up_step = self._step_upload(file_info)
        if up_step is False:
            self.result.pages_failed.append(file_info.to_dict())
            return False

        elif up_step is None:
            logger.debug("file %s exists", file_info.cropped_filename)

        uploaded = up_step is True

        # Step 4 & 5 - Update wikitext references
        updated = self.update_file_references(file_info)

        if uploaded:
            self.result.pages_uploaded.append(file_info.to_dict())
            return True

        elif updated:
            self.result.pages_updated.append(file_info.to_dict())
            return True

        file_info.status = "completed"
        self.result.pages_processed.append(file_info.to_dict())
        return False

    def _check_file_exists(self, cropped_filename):
        file_exists = self.exists.get(cropped_filename.removeprefix("File:"))
        if file_exists is None:
            file_exists = MwClientPage(cropped_filename, self.site).exists()
        return file_exists

    def update_file_references(self, file_info: CropFileProcessingInfo) -> bool:
        # Step 4 - Update original file wikitext
        updated = self._step_update_original(file_info)

        # Step 5 - Update template page reference
        updated2 = self._step_update_page_reference(
            file_info,
            file_info.template_title,
            "update_template",
        )

        # Step 6 - Update corresponding content page
        template_title = file_info.template_title
        if template_title.lower().startswith("template:"):
            updated3 = self._step_update_page_reference(
                file_info,
                template_title[9:],
                "update_page",
            )
        else:
            self._skip_step(file_info, "update_page", "Skipped - title does not start with Template:")
            updated3 = False

        return updated or updated2 or updated3

    # ------------------------------------------------------------------
    # Individual pipeline steps
    # ------------------------------------------------------------------

    def _step_download(self, file_info: CropFileProcessingInfo, template: TemplateRecord) -> bool:
        """Download the original file. Returns True on success."""
        try:
            session = create_commons_session(settings.other.user_agent)
            download_result = download_file_for_cropping(
                template.last_world_file,
                self.original_dir,
                session=session,
            )
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.exception("Job %s: Exception downloading %s", self.job_id, template.last_world_file)
            self._fail(file_info, "download", error_msg)
            return False

        if download_result["success"]:
            downloaded_path = download_result["path"]
            file_info.steps["download"] = {"result": True, "msg": f"Downloaded to {downloaded_path}"}
            file_info.downloaded_path = downloaded_path
            return True

        error_msg = download_result.get("error", "Unknown download error")
        logger.warning("Job %s: Failed to download %s", self.job_id, template.last_world_file)
        self._fail(file_info, "download", error_msg)
        return False

    def _step_crop(
        self,
        file_info: CropFileProcessingInfo,
        template: TemplateRecord,
        cropped_path: Path,
    ) -> bool:
        """Crop the SVG. Returns True on success."""
        crop_result = crop_svg_file(Path(file_info.downloaded_path), cropped_path)

        if not crop_result["success"]:
            error_msg = crop_result.get("error", "Unknown crop error")
            logger.warning("Job %s: Failed to crop %s", self.job_id, template.last_world_file)
            self._fail(file_info, "crop", error_msg)
            return False

        file_info.steps["crop"] = {"result": True, "msg": f"Cropped to {cropped_path}"}
        file_info.cropped_path = cropped_path
        self.result.summary.cropped += 1
        return True

    def _step_upload(self, file_info: CropFileProcessingInfo) -> bool | None:
        """Upload the cropped file. Returns True if upload succeeded or was skipped."""
        file_name = ensure_file_prefix(file_info.original_file)
        wikitext = MwClientPage(file_name, self.site).get_text()
        cropped_file_wikitext = create_cropped_file_text(file_info.original_file, wikitext)

        upload_result = upload_cropped_file(
            file_info.cropped_filename,
            Path(file_info.cropped_path),
            self.site,
            cropped_file_wikitext,
        )

        if upload_result.get("file_exists"):
            logger.warning(
                "Job %s: Skipped upload for %s (file already exists on Commons)",
                self.job_id,
                file_info.cropped_filename,
            )
            self._skip_step(file_info, "upload_cropped", "Skipped - file already exists on Commons")
            file_info.status = "skipped"
            self.result.summary.skipped += 1
            # Still continue to wikitext updates even if file existed
            return None

        if upload_result["success"]:
            logger.info("Job %s: Successfully uploaded %s", self.job_id, file_info.cropped_filename)
            file_info.steps["upload_cropped"] = {"result": True, "msg": f"Uploaded as {file_info.cropped_filename}"}
            file_info.status = "uploaded"
            self.result.summary.uploaded += 1
            return True

        error = upload_result.get("error", "Unknown upload error")
        logger.warning("Job %s: Failed to upload %s", self.job_id, file_info.cropped_filename)

        self._skip_step(file_info, "update_original", "Skipped - upload failed")
        self._skip_step(file_info, "update_template", "Skipped - upload was not successful")
        self._skip_step(file_info, "update_page", "Skipped - upload was not successful")

        self._fail(file_info, "upload_cropped", error)
        file_info.cropped_filename = ""
        return False

    def _step_update_original(self, file_info: CropFileProcessingInfo) -> bool:
        """Update the original file's wikitext to reference the cropped version."""
        original_file_name = ensure_file_prefix(file_info.original_file)
        original_page = MwClientPage(original_file_name, self.site)

        wikitext = original_page.get_text()
        updated_text = update_original_file_text(file_info.cropped_filename, wikitext)

        if wikitext == updated_text:
            logger.info("Job %s: No update needed for original file text of %s", self.job_id, file_info.original_file)
            file_info.steps["update_original"] = {"result": None, "msg": "No update needed"}
            return False

        update_result = original_page.edit(
            updated_text,
            summary="Adding/updating {{Image extracted}}",
        )

        if update_result["success"]:
            file_info.steps["update_original"] = {
                "result": True,
                "msg": "Updated original file wikitext",
                "newrevid": update_result.get("newrevid", 0),
            }
            return True

        error = update_result.get("error", "Unknown error")
        logger.warning(
            "Job %s: Failed to update original file text for %s (reason: %s)",
            self.job_id,
            file_info.original_file,
            error,
        )
        # self._fail(file_info, "update_original", error)
        file_info.steps["update_original"] = {"result": False, "msg": error}
        return False

    def _step_update_page_reference(
        self,
        file_info: CropFileProcessingInfo,
        page_title: str,
        step_name: str,
    ) -> bool:
        """Update a page to reference the cropped file."""

        page = MwClientPage(page_title, self.site)

        if not page.exists():
            logger.warning("Job %s: Page does not exist: %s", self.job_id, page_title)
            file_info.steps[step_name] = {
                "result": None,
                "msg": f"Page does not exist: {page_title}",
            }
            return False

        page_text = page.get_text()

        if not page_text:
            logger.warning("Job %s: Empty page text for %s", self.job_id, page_title)
            file_info.steps[step_name] = {
                "result": False,
                "msg": f"Empty page text: {page_title}",
            }
            return False

        updated_text = update_template_page_file_reference(
            file_info.original_file,
            file_info.cropped_filename,
            page_text,
        )

        if page_text == updated_text:
            logger.info("Job %s: No update needed for page %s", self.job_id, page_title)
            file_info.steps[step_name] = {
                "result": None,
                "msg": "No update needed",
            }
            return False

        summary = f"Update file reference to [[File:{file_info.cropped_filename.removeprefix('File:')}]]"

        update_result = page.edit(updated_text, summary)

        if update_result.get("success"):
            file_info.steps[step_name] = {
                "result": True,
                "msg": f"Updated page {page_title}",
                "newrevid": update_result.get("newrevid", 0),
            }
            return True

        error = update_result.get("error", "Unknown error")

        logger.warning("Job %s: Failed to update page %s (reason: %s)", self.job_id, page_title, error)

        file_info.steps[step_name] = {
            "result": False,
            "msg": f"Failed to update page {page_title}: {error}",
        }

        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _skip_process(self, file_info: CropFileProcessingInfo) -> None:
        self._skip_step(file_info, "download", "Skipped - file already exists on Commons")
        self._skip_step(file_info, "crop", "Skipped - file already exists on Commons")
        self._skip_step(file_info, "upload_cropped", "Skipped - file already exists on Commons")

    def _fail(self, file_info: CropFileProcessingInfo, step: str, error: str) -> None:
        """Mark a step and the file as failed, and increment the summary counter."""
        file_info.steps[step] = {"result": False, "msg": error}
        file_info.status = "failed"
        file_info.error = error
        self.result.summary.failed += 1

    def _skip_step(self, file_info: CropFileProcessingInfo, step: str, reason: str) -> None:
        """Mark a step as skipped (result=None)."""
        file_info.steps[step] = {"result": None, "msg": reason}

    def _skip_upload_steps(self, file_info: CropFileProcessingInfo) -> None:
        for step in ("upload_cropped", "update_original", "update_template", "update_page"):
            self._skip_step(file_info, step, "Skipped - upload disabled")
        file_info.status = "skipped"
        self.result.summary.skipped += 1
        logger.info("Job %s: Skipped upload for %s (upload disabled)", self.job_id, file_info.cropped_filename)
        file_info.cropped_filename = ""


__all__ = [
    "CropMainFilesWorker",
]
