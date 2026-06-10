"""
Worker module for cropping main files and uploading them with (cropped) suffix.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import mwclient

from ....api_services.clients import create_commons_session, get_user_site
from ....api_services.mwclient_page import MwClientPage
from ....api_services.query_api import is_pages_exists
from ....config import settings
from ....db.models import TemplateRecord
from ....db.services import list_templates
from ....utils.wikitext import (
    create_cropped_file_text,
    ensure_file_prefix,
    update_original_file_text,
    update_template_page_file_reference,
)
from ...base_worker import BaseJobWorker
from .crop_file import crop_svg_file
from .crop_utils import generate_cropped_filename
from .download import download_file_for_cropping
from .upload import upload_cropped_file

logger = logging.getLogger(__name__)

StepResult = dict[str, Any]


@dataclass
class TemplateProcessingInfo:
    """Holds all state for a single file being processed."""

    template_id: int
    template_title: str
    original_file: str
    cropped_filename: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    error: str | None = None
    downloaded_path: Path | None = None
    cropped_path: Path | None = None
    steps: dict[str, StepResult] = field(
        default_factory=lambda: {
            "download": {"result": None, "msg": ""},
            "crop": {"result": None, "msg": ""},
            "upload_cropped": {"result": None, "msg": ""},
            "update_original": {"result": None, "msg": ""},
            "update_template": {"result": None, "msg": ""},
            "update_page": {"result": None, "msg": ""},
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_title": self.template_title,
            "original_file": self.original_file,
            "cropped_filename": self.cropped_filename,
            "timestamp": self.timestamp,
            "status": self.status,
            "error": self.error,
            "downloaded_path": str(self.downloaded_path) if self.downloaded_path else None,
            "cropped_path": str(self.cropped_path) if self.cropped_path else None,
            "steps": self.steps,
        }


class CropMainFilesWorker(BaseJobWorker):
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
        self.job_id = job_id
        self.user = user
        self.site: mwclient.Site | None = None
        self.args = args or {}
        try:
            self.upload_limit = (
                int(self.args.get("upload_limit")) if self.args.get("upload_limit") is not None else None
            )
        except (ValueError, TypeError):
            self.upload_limit = None
        self.upload_files = bool(self.args.get("upload_files"))

        super().__init__(job_id, user, cancel_event)
        self.result: Dict[str, Any] = self.get_initial_result()

        self.exists = {}
        self.original_dir = Path(settings.paths.crop_main_files_path) / "original"
        self.cropped_dir = Path(settings.paths.crop_main_files_path) / "cropped"

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "crop_main_files"

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
                "cropped": 0,
                "uploaded": 0,
                "updated": 0,
                "skipped": 0,
                "failed": 0,
            },
            "pages_processed": [],
            "pages_uploaded": [],
            "pages_updated": [],
            "pages_skipped": [],
            "pages_failed": [],
        }

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
        logger.info(f"Job {self.job_id}: Found {len(templates)} templates with main files")

        self._check_exists(templates)

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

    def _check_exists(self, templates) -> None:
        cropped_filenames = [generate_cropped_filename(template.last_world_file) for template in templates]
        exists_files = is_pages_exists(cropped_filenames, self.site)

        for file in exists_files:
            self.exists[file.removeprefix("File:")] = exists_files[file]

        logger.info(f"self.exists: {len(self.exists)}")

    def _load_templates(self) -> list[TemplateRecord]:
        templates = list_templates()
        _templates = [t for t in templates if t.last_world_file]
        return self._apply_limits(_templates)

    def _apply_limits(self, templates: list[TemplateRecord]) -> list[TemplateRecord]:
        _limit = self.upload_limit if isinstance(self.upload_limit, int) else 0
        if _limit > 0 and len(templates) > _limit:
            logger.info(f"Job {self.job_id}: limiting from {len(templates)} to {_limit} item")
            return templates[:_limit]

        return templates

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------
    def _process_template(self, template: TemplateRecord) -> bool:
        self.result["summary"]["processed"] += 1

        cropped_filename = generate_cropped_filename(template.last_world_file)

        # file info
        file_info = TemplateProcessingInfo(
            template_id=template.id,
            template_title=template.title,
            original_file=template.last_world_file,
            cropped_filename=cropped_filename,
        )

        # pre steps if the file already in commons, skip download/upload files.
        if self._check_file_exists(cropped_filename):
            self._skip_process(file_info)
            # Step 4 & 5 - Update wikitext references
            updated = self.update_file_references(file_info)

            if updated:
                file_info.status = "completed"
                self.result["summary"]["updated"] += 1
                self._append(file_info, key="pages_updated")
                return True
            else:
                # if all file_info.steps "result" is None do:
                if all(step["result"] is None for step in file_info.steps.values()):
                    file_info.status = "skipped"
                    self.result["summary"]["skipped"] += 1

            self._append(file_info, key="pages_skipped")
            return False

        # ----------------------------------
        # Step 1 - Download
        if not self._step_download(file_info, template):
            self._append(file_info, key="pages_failed")
            return False

        # ----------------------------------
        # Step 2 - Crop
        cropped_output_path = self.cropped_dir / Path(cropped_filename.removeprefix("File:")).name
        if not self._step_crop(file_info, template, cropped_output_path):
            self._append(file_info, key="pages_failed")
            return False

        # Upload disabled → mark skipped and move on
        if not self.upload_files:
            self._skip_upload_steps(file_info)
            self._append(file_info, key="pages_skipped")
            return False

        # ----------------------------------
        # Step 3 - Upload cropped file
        up_step = self._step_upload(file_info)
        if up_step is False:
            self._append(file_info, key="pages_failed")
            return False

        elif up_step is None:
            logger.debug(f"file {file_info.cropped_filename} exists")

        uploaded = up_step is True

        # Step 4 & 5 - Update wikitext references
        updated = self.update_file_references(file_info)

        if uploaded:
            self._append(file_info, key="pages_uploaded")
            return True

        elif updated:
            self._append(file_info, key="pages_updated")
            return True

        file_info.status = "completed"
        self._append(file_info, key="pages_processed")
        return False

    def _check_file_exists(self, cropped_filename):
        file_exists = self.exists.get(cropped_filename.removeprefix("File:"))
        if file_exists is None:
            file_exists = MwClientPage(cropped_filename, self.site).exists()
        return file_exists

    def update_file_references(self, file_info: TemplateProcessingInfo) -> bool:
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

    def _step_download(self, file_info: TemplateProcessingInfo, template: TemplateRecord) -> bool:
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
            logger.exception(f"Job {self.job_id}: Exception downloading {template.last_world_file}")
            self._fail(file_info, "download", error_msg)
            return False

        if download_result["success"]:
            downloaded_path = download_result["path"]
            file_info.steps["download"] = {"result": True, "msg": f"Downloaded to {downloaded_path}"}
            file_info.downloaded_path = downloaded_path
            return True

        error_msg = download_result.get("error", "Unknown download error")
        logger.warning(f"Job {self.job_id}: Failed to download {template.last_world_file}")
        self._fail(file_info, "download", error_msg)
        return False

    def _step_crop(
        self,
        file_info: TemplateProcessingInfo,
        template: TemplateRecord,
        cropped_path: Path,
    ) -> bool:
        """Crop the SVG. Returns True on success."""
        crop_result = crop_svg_file(file_info.downloaded_path, cropped_path)

        if not crop_result["success"]:
            error_msg = crop_result.get("error", "Unknown crop error")
            logger.warning(f"Job {self.job_id}: Failed to crop {template.last_world_file}")
            self._fail(file_info, "crop", error_msg)
            return False

        file_info.steps["crop"] = {"result": True, "msg": f"Cropped to {cropped_path}"}
        file_info.cropped_path = cropped_path
        self.result["summary"]["cropped"] += 1
        return True

    def _step_upload(self, file_info: TemplateProcessingInfo) -> bool | None:
        """Upload the cropped file. Returns True if upload succeeded or was skipped."""
        file_name = ensure_file_prefix(file_info.original_file)
        wikitext = MwClientPage(file_name, self.site).get_text()
        cropped_file_wikitext = create_cropped_file_text(file_info.original_file, wikitext)

        upload_result = upload_cropped_file(
            file_info.cropped_filename,
            file_info.cropped_path,
            self.site,
            cropped_file_wikitext,
        )

        if upload_result.get("file_exists"):
            logger.warning(
                f"Job {self.job_id}: Skipped upload for {file_info.cropped_filename} (file already exists on Commons)"
            )
            self._skip_step(file_info, "upload_cropped", "Skipped - file already exists on Commons")
            file_info.status = "skipped"
            self.result["summary"]["skipped"] += 1
            # Still continue to wikitext updates even if file existed
            return None

        if upload_result["success"]:
            logger.info(f"Job {self.job_id}: Successfully uploaded {file_info.cropped_filename}")
            file_info.steps["upload_cropped"] = {"result": True, "msg": f"Uploaded as {file_info.cropped_filename}"}
            file_info.status = "uploaded"
            self.result["summary"]["uploaded"] += 1
            return True

        error = upload_result.get("error", "Unknown upload error")
        logger.warning(f"Job {self.job_id}: Failed to upload {file_info.cropped_filename}")

        self._skip_step(file_info, "update_original", "Skipped - upload failed")
        self._skip_step(file_info, "update_template", "Skipped - upload was not successful")
        self._skip_step(file_info, "update_page", "Skipped - upload was not successful")

        self._fail(file_info, "upload_cropped", error)
        file_info.cropped_filename = None
        return False

    def _step_update_original(self, file_info: TemplateProcessingInfo) -> bool:
        """Update the original file's wikitext to reference the cropped version."""
        original_file_name = ensure_file_prefix(file_info.original_file)
        original_page = MwClientPage(original_file_name, self.site)

        wikitext = original_page.get_text()
        updated_text = update_original_file_text(file_info.cropped_filename, wikitext)

        if wikitext == updated_text:
            logger.info(f"Job {self.job_id}: No update needed for original file text of {file_info.original_file}")
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
            f"Job {self.job_id}: Failed to update original file text for {file_info.original_file} (reason: {error})"
        )
        # self._fail(file_info, "update_original", error)
        file_info.steps["update_original"] = {"result": False, "msg": error}
        return False

    def _step_update_page_reference(
        self,
        file_info: TemplateProcessingInfo,
        page_title: str,
        step_name: str,
    ) -> bool:
        """Update a page to reference the cropped file."""

        page = MwClientPage(page_title, self.site)

        if not page.exists():
            logger.warning(f"Job {self.job_id}: Page does not exist: {page_title}")
            file_info.steps[step_name] = {
                "result": None,
                "msg": f"Page does not exist: {page_title}",
            }
            return False

        page_text = page.get_text()

        if not page_text:
            logger.warning(f"Job {self.job_id}: Empty page text for {page_title}")
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
            logger.info(f"Job {self.job_id}: No update needed for page {page_title}")
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

        logger.warning(f"Job {self.job_id}: Failed to update page {page_title} (reason: {error})")

        file_info.steps[step_name] = {
            "result": False,
            "msg": f"Failed to update page {page_title}: {error}",
        }

        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _skip_process(self, file_info: TemplateProcessingInfo) -> None:
        self._skip_step(file_info, "download", "Skipped - file already exists on Commons")
        self._skip_step(file_info, "crop", "Skipped - file already exists on Commons")
        self._skip_step(file_info, "upload_cropped", "Skipped - file already exists on Commons")

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
        for step in ("upload_cropped", "update_original", "update_template", "update_page"):
            self._skip_step(file_info, step, "Skipped - upload disabled")
        file_info.status = "skipped"
        self.result["summary"]["skipped"] += 1
        logger.info(f"Job {self.job_id}: Skipped upload for {file_info.cropped_filename} (upload disabled)")
        file_info.cropped_filename = None

    def _append(self, file_info: TemplateProcessingInfo, key: str = "pages_processed") -> None:
        self.result[key].append(file_info.to_dict())


# ------------------------------------------------------------------
# Backwards-compatible entry-point
# ------------------------------------------------------------------


def crop_main_files_worker_entry(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """
    Entry point for crop newest world files background job.

    Args:
        job_id: The job ID
        user: User authentication data for OAuth uploads
        cancel_event: Threading event for cancellation
        args: Optional arguments dict (unused, for unified signature)
    """
    if args and args.get("crop_newest_upload_limit"):
        args.update({"upload_limit": args.get("crop_newest_upload_limit")})

    worker = CropMainFilesWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "crop_main_files_worker_entry",
    "CropMainFilesWorker",
]
