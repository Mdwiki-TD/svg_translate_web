"""
Processor class for cropping main files and uploading them with (cropped) suffix.
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
from ...utils.commons_client import create_commons_session
from ...utils.text_api import get_file_text, get_page_text, update_file_text, update_page_text
from ...utils.wiki_client import get_user_site
from .. import jobs_service
from .crop_file import crop_svg_file
from .download import download_file_for_cropping
from .upload import upload_cropped_file
from .utils import generate_cropped_filename
from ...utils.wikitext import create_cropped_file_text, update_original_file_text, update_template_page_file_reference

logger = logging.getLogger(__name__)

StepResult = dict[str, Any]


@dataclass
class FileProcessingInfo:
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


def is_cropped_file_existing(
    cropped_filename: str,
    site: mwclient.Site | None,
) -> bool:

    page = site.Pages[cropped_filename]

    if page.exists:
        logger.error(f"Warning: File {cropped_filename} already exists on Commons")
        return True
    return False


class CropMainFilesProcessor:
    """
    Orchestrates the full pipeline for cropping SVG files and uploading them to Commons.

    Pipeline steps per file:
        1. Download  – fetch the original file from Commons
        2. Crop      – crop the SVG to its bounding-box
        3. Upload    – upload the cropped version under a new filename
        4. Update original  – add a link to the cropped file in the original file's wikitext
        5. Update template  – point the template page at the cropped file
    """

    def __init__(
        self,
        job_id: int,
        result: dict[str, Any],
        result_file: str,
        user: dict[str, Any] | None,
        *,
        cancel_event: threading.Event | None = None,
        upload_files: bool = False,
    ) -> None:
        self.job_id = job_id
        self.result = result
        self.result_file = result_file
        self.user = user
        self.cancel_event = cancel_event
        self.upload_files = upload_files

        self.site: mwclient.Site | None = None
        self.session: requests.Session | None = None
        self.original_dir = Path(settings.paths.crop_main_files_path) / "original"
        self.cropped_dir = Path(settings.paths.crop_main_files_path) / "cropped"

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
                jobs_service.save_job_result_by_name(self.result_file, self.result)

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
                job_type="crop_main_files"
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
        templates_with_files = [t for t in templates if t.last_world_file]
        return self._apply_limits(templates_with_files)

    def _apply_limits(self, templates: list[TemplateRecord]) -> list[TemplateRecord]:
        upload_limit = int(settings.dynamic.get("crop_newest_upload_limit", 0))
        if upload_limit > 0 and len(templates) > upload_limit:
            logger.info(
                f"Job {self.job_id}: Upload cropped files limit – "
                f"limiting from {len(templates)} to {upload_limit} files"
            )
            return templates[:upload_limit]

        dev_limit = settings.download.dev_limit
        if dev_limit > 0 and len(templates) > dev_limit:
            logger.info(
                f"Job {self.job_id}: Development mode – "
                f"limiting from {len(templates)} to {dev_limit} files"
            )
            return templates[:dev_limit]

        return templates

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------

    def _process_template(self, template: TemplateRecord) -> None:
        cropped_filename = generate_cropped_filename(template.last_world_file)
        file_info = FileProcessingInfo(
            template_id=template.id,
            template_title=template.title,
            original_file=template.last_world_file,
            cropped_filename=cropped_filename,
        )

        # pre steps if the file already in commons, skip download/upload files.
        if is_cropped_file_existing(cropped_filename, self.site):
            self._skip_step(file_info, "download", "Skipped – file already exists on Commons")
            self._skip_step(file_info, "crop", "Skipped – file already exists on Commons")
            self._skip_step(file_info, "upload_cropped", "Skipped – file already exists on Commons")

            # Step 4 & 5 – Update wikitext references
            self.update_file_references(file_info)

            self._append(file_info)
            return

        # Step 1 – Download
        if not self._step_download(file_info, template):
            self._append(file_info)
            return

        # Step 2 – Crop
        cropped_output_path = self.cropped_dir / Path(cropped_filename.removeprefix("File:")).name
        if not self._step_crop(file_info, template, cropped_output_path):
            self._append(file_info)
            return

        # Upload disabled → mark skipped and move on
        if not self.upload_files:
            self._skip_upload_steps(file_info)
            self._append(file_info)
            return

        # Step 3 – Upload cropped file
        if not self._step_upload(file_info):
            self._append(file_info)
            return

        # Step 4 & 5 – Update wikitext references
        self.update_file_references(file_info)

        self._append(file_info)

    def update_file_references(self, file_info):

        # Step 4 – Update original file wikitext
        self._step_update_original(file_info)

        # Step 5 – Update template page reference
        self._step_update_template(file_info)

    # ------------------------------------------------------------------
    # Individual pipeline steps
    # ------------------------------------------------------------------

    def _step_download(self, file_info: FileProcessingInfo, template: TemplateRecord) -> bool:
        """Download the original file. Returns True on success."""
        try:
            download_result = download_file_for_cropping(
                template.last_world_file,
                self.original_dir,
                session=self.session,
            )
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            logger.exception(f"Job {self.job_id}: Exception downloading {template.last_world_file}")
            self._fail(file_info, "download", error_msg)
            return False

        if not download_result["success"]:
            error_msg = download_result.get("error", "Unknown download error")
            logger.warning(f"Job {self.job_id}: Failed to download {template.last_world_file}")
            self._fail(file_info, "download", error_msg)
            return False

        downloaded_path = download_result["path"]
        file_info.steps["download"] = {
            "result": True,
            "msg": f"Downloaded to {downloaded_path}"
        }
        file_info.downloaded_path = downloaded_path
        self.result["summary"]["processed"] += 1
        return True

    def _step_crop(
        self,
        file_info: FileProcessingInfo,
        template: TemplateRecord,
        cropped_output_path: Path,
    ) -> bool:
        """Crop the SVG. Returns True on success."""
        crop_result = crop_svg_file(file_info.downloaded_path, cropped_output_path)

        if not crop_result["success"]:
            error_msg = crop_result.get("error", "Unknown crop error")
            logger.warning(f"Job {self.job_id}: Failed to crop {template.last_world_file}")
            self._fail(file_info, "crop", error_msg)
            return False

        file_info.steps["crop"] = {"result": True, "msg": f"Cropped to {cropped_output_path}"}
        file_info.cropped_path = cropped_output_path
        self.result["summary"]["cropped"] += 1
        return True

    def _step_upload(self, file_info: FileProcessingInfo) -> bool:
        """Upload the cropped file. Returns True if upload succeeded or was skipped."""
        wikitext = get_file_text(file_info.original_file, self.site)
        cropped_file_wikitext = create_cropped_file_text(file_info.original_file, wikitext)

        upload_result = upload_cropped_file(
            file_info.cropped_filename,
            file_info.cropped_path,
            self.site,
            cropped_file_wikitext,
        )

        if upload_result.get("file_exists"):
            logger.warning(
                f"Job {self.job_id}: Skipped upload for {file_info.cropped_filename} "
                "(file already exists on Commons)"
            )
            self._skip_step(file_info, "upload_cropped", "Skipped – file already exists on Commons")
            file_info.status = "skipped"
            self.result["summary"]["skipped"] += 1
            # Still continue to wikitext updates even if file existed
            return True

        if not upload_result["success"]:
            error = upload_result.get("error", "Unknown upload error")
            logger.warning(f"Job {self.job_id}: Failed to upload {file_info.cropped_filename}")

            self._skip_step(file_info, "update_original", "Skipped – upload failed")
            self._skip_step(file_info, "update_template", "Skipped – upload was not successful")

            self._fail(file_info, "upload_cropped", error)
            file_info.cropped_filename = None
            return False

        logger.info(f"Job {self.job_id}: Successfully uploaded {file_info.cropped_filename}")
        file_info.steps["upload_cropped"] = {"result": True, "msg": f"Uploaded as {file_info.cropped_filename}"}
        file_info.status = "uploaded"
        self.result["summary"]["uploaded"] += 1
        return True

    def _step_update_original(self, file_info: FileProcessingInfo) -> None:
        """Update the original file's wikitext to reference the cropped version."""
        wikitext = get_file_text(file_info.original_file, self.site)
        updated_text = update_original_file_text(file_info.cropped_filename, wikitext)

        if wikitext == updated_text:
            logger.info(f"Job {self.job_id}: No update needed for original file text of {file_info.original_file}")
            file_info.steps["update_original"] = {"result": None, "msg": "No update needed"}
            return

        update_result = update_file_text(file_info.original_file, updated_text, self.site)
        if not update_result["success"]:
            error = update_result.get("error", "Unknown error")
            logger.warning(
                f"Job {self.job_id}: Failed to update original file text for "
                f"{file_info.original_file} (reason: {error})"
            )
            # self._fail(file_info, "update_original", error)
            file_info.steps["update_original"] = {"result": False, "msg": error}
        else:
            file_info.steps["update_original"] = {"result": True, "msg": "Updated original file wikitext"}

    def _step_update_template(self, file_info: FileProcessingInfo) -> None:
        """Update the template page to reference the cropped file."""
        template_title = file_info.template_title
        template_text = get_page_text(template_title, self.site)
        updated_text = update_template_page_file_reference(
            file_info.original_file, file_info.cropped_filename, template_text
        )

        if template_text == updated_text:
            logger.info(f"Job {self.job_id}: No update needed for template page {template_title}")
            file_info.steps["update_template"] = {"result": None, "msg": "No update needed"}
            return

        summary = f"Update file reference to [[File:{file_info.cropped_filename.removeprefix('File:')}]]"
        update_result = update_page_text(template_title, updated_text, self.site, summary=summary)

        if not update_result["success"]:
            error = update_result.get("error", "Unknown error")
            logger.warning(
                f"Job {self.job_id}: Failed to update template page {template_title} "
                f"(reason: {error})"
            )
            # self._fail(file_info, "update_template", f"Failed to update template {template_title}")
            file_info.steps["update_template"] = {"result": False, "msg": f"Failed to update template {template_title}"}
        else:
            file_info.steps["update_template"] = {"result": True, "msg": f"Updated template {template_title}"}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fail(self, file_info: FileProcessingInfo, step: str, error: str) -> None:
        """Mark a step and the file as failed, and increment the summary counter."""
        file_info.steps[step] = {"result": False, "msg": error}
        file_info.status = "failed"
        file_info.error = error
        self.result["summary"]["failed"] += 1

    def _skip_step(self, file_info: FileProcessingInfo, step: str, reason: str) -> None:
        """Mark a step as skipped (result=None)."""
        file_info.steps[step] = {"result": None, "msg": reason}

    def _skip_upload_steps(self, file_info: FileProcessingInfo) -> None:
        for step in ("upload_cropped", "update_original", "update_template"):
            self._skip_step(file_info, step, "Skipped – upload disabled")
        file_info.status = "skipped"
        file_info.cropped_filename = None
        self.result["summary"]["skipped"] += 1
        logger.info(f"Job {self.job_id}: Skipped upload for {file_info.cropped_filename} (upload disabled)")

    def _is_cancelled(self) -> bool:
        if self.cancel_event and self.cancel_event.is_set():
            logger.info(f"Job {self.job_id}: Cancellation detected, stopping.")
            self.result["status"] = "cancelled"
            self.result["cancelled_at"] = datetime.now().isoformat()
            return True
        return False

    def _append(self, file_info: FileProcessingInfo) -> None:
        self.result["files_processed"].append(file_info.to_dict())

    def _finalize(self) -> None:
        # Mark as completed if not cancelled or failed
        if self.result.get("status") != "cancelled":
            self.result["status"] = "completed"
            logger.info(f"Job {self.job_id}: Crop processing completed")


# ------------------------------------------------------------------
# Backwards-compatible entry-point
# ------------------------------------------------------------------

def process_crops(
    job_id: int,
    result: dict[str, Any],
    result_file: str,
    user: dict[str, Any] | None,
    cancel_event: threading.Event | None = None,
    upload_files: bool = False,
) -> dict[str, Any]:
    """Thin shim kept for backwards compatibility."""
    processor = CropMainFilesProcessor(
        job_id=job_id,
        result=result,
        result_file=result_file,
        user=user,
        cancel_event=cancel_event,
        upload_files=upload_files,
    )
    return processor.run()


__all__ = [
    "CropMainFilesProcessor",
    "process_crops",
]
