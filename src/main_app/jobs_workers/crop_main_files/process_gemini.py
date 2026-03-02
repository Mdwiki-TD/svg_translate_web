"""
Worker module for cropping main files and uploading them with (cropped) suffix.
"""

from __future__ import annotations

import logging
import threading
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
from .wikitext import create_cropped_file_text, update_original_file_text, update_template_page_file_reference

logger = logging.getLogger(__name__)


class CropWorker:
    """
    Worker class for downloading, cropping, and uploading template files.
    """

    def __init__(
        self,
        job_id: int,
        result: dict[str, Any],
        result_file: str,
        user: dict[str, Any] | None,
        cancel_event: threading.Event | None = None,
        upload_files: bool = False,
    ):
        self.job_id = job_id
        self.result = result
        self.result_file = result_file
        self.user = user
        self.cancel_event = cancel_event
        self.upload_files = upload_files

        self.site: mwclient.Site | None = None
        self.session: requests.Session | None = None

        base_path = Path(settings.paths.crop_main_files_path)
        self.original_dir = base_path / "original"
        self.cropped_dir = base_path / "cropped"

    # ==========================================
    # Main Execution Loop
    # ==========================================

    def execute(self) -> dict[str, Any]:
        """Main entry point that coordinates the job execution."""
        if not self._initialize_job():
            return self.result

        templates = self._get_templates_to_process()
        self._set_total_templates(len(templates))

        for n, template in enumerate(templates, start=1):
            if self._should_cancel():
                break

            self._save_progress_if_needed(n)
            self._log_template_processing(n, len(templates), template)

            # Run the strict pipeline for a single template
            file_info = self._process_single_template(template)

            self._update_job_summary_counters(file_info)

        self._finalize_job()
        return self.result

    def _process_single_template(self, template: TemplateRecord) -> dict[str, Any]:
        """Runs the step-by-step pipeline for an individual template."""
        file_info = self._initialize_file_info(template)

        # Pipeline steps (Early return if any step fails/skips)
        if not self._step_download(template, file_info):
            return file_info

        if not self._step_crop(template, file_info):
            return file_info

        if not self._step_upload(template, file_info):
            return file_info

        self._step_update_original_wikitext(template, file_info)
        self._step_update_template_reference(template, file_info)

        # If it passed all steps, mark as successfully uploaded
        self._mark_as_uploaded(file_info)
        return file_info

    # ==========================================
    # Pipeline Steps
    # ==========================================

    def _step_download(self, template: TemplateRecord, file_info: dict[str, Any]) -> bool:
        """Step 1: Download the original file."""
        try:
            res = download_file_for_cropping(template.last_world_file, self.original_dir, session=self.session)
            if not res["success"]:
                return self._fail_file(file_info, "download", res.get("error", "Unknown download error"))

            file_info["downloaded_path"] = res["path"]
            file_info["steps"]["download"] = {"result": True, "msg": f"Downloaded to {res['path']}"}
            return True
        except Exception as e:
            logger.exception(f"Job {self.job_id}: Exception processing {template.last_world_file}")
            return self._fail_file(file_info, "download", f"{type(e).__name__}: {str(e)}")

    def _step_crop(self, template: TemplateRecord, file_info: dict[str, Any]) -> bool:
        """Step 2: Crop the downloaded image."""
        downloaded_path = file_info["downloaded_path"]
        cropped_filename_path = Path(file_info["cropped_filename"].removeprefix("File:")).name
        cropped_output_path = self.cropped_dir / cropped_filename_path

        res = crop_svg_file(downloaded_path, cropped_output_path)
        if not res["success"]:
            return self._fail_file(file_info, "crop", res.get("error", "Unknown crop error"))

        file_info["cropped_path"] = cropped_output_path
        file_info["steps"]["crop"] = {"result": True, "msg": f"Cropped to {cropped_output_path}"}
        return True

    def _step_upload(self, template: TemplateRecord, file_info: dict[str, Any]) -> bool:
        """Step 3 & 4: Check rules and Upload the cropped image."""
        if not self.upload_files:
            return self._skip_file(file_info, "upload_cropped", "Skipped – upload disabled")

        original_file = template.last_world_file
        cropped_filename = file_info["cropped_filename"]
        cropped_path = file_info["cropped_path"]

        wikitext = get_file_text(original_file, self.site)
        cropped_file_wikitext = create_cropped_file_text(original_file, wikitext)

        res = upload_cropped_file(cropped_filename, cropped_path, self.site, cropped_file_wikitext)

        if res.get("file_exists"):
            logger.warning(f"Job {self.job_id}: Skipped upload for {cropped_filename} (already exists)")
            return self._skip_file(file_info, "upload_cropped", "Skipped – file already exists on Commons")

        if not res["success"]:
            error = res.get("error", "Unknown upload error")
            logger.warning(f"Job {self.job_id}: Failed to upload {cropped_filename}")
            return self._fail_file(file_info, "upload_cropped", error, skip_rest="Skipped – upload failed")

        logger.info(f"Job {self.job_id}: Successfully uploaded {cropped_filename}")
        file_info["steps"]["upload_cropped"] = {"result": True, "msg": f"Uploaded as {cropped_filename}"}
        return True

    def _step_update_original_wikitext(self, template: TemplateRecord, file_info: dict[str, Any]) -> bool:
        """Step 5: Update the original file's wikitext to point to the new crop."""
        original_file = template.last_world_file
        cropped_filename = file_info["cropped_filename"]

        wikitext = get_file_text(original_file, self.site)
        updated_text = update_original_file_text(cropped_filename, wikitext)

        if wikitext == updated_text:
            logger.info(f"Job {self.job_id}: No update needed for original file text of {original_file}")
            file_info["steps"]["update_original"] = {"result": None, "msg": "No update needed"}
            return True

        res = update_file_text(original_file, updated_text, self.site)
        if not res["success"]:
            error = res.get("error", "Unknown error")
            logger.warning(f"Job {self.job_id}: Failed to update original text for {original_file} (reason: {error})")
            file_info["steps"]["update_original"] = {"result": False, "msg": error}
            return False

        file_info["steps"]["update_original"] = {"result": True, "msg": "Updated original file wikitext"}
        return True

    def _step_update_template_reference(self, template: TemplateRecord, file_info: dict[str, Any]) -> bool:
        """Step 6: Update the template page to use the newly cropped file."""
        original_file = template.last_world_file
        cropped_filename = file_info["cropped_filename"]
        template_title = template.title

        template_text = get_page_text(template_title, self.site)
        updated_text = update_template_page_file_reference(original_file, cropped_filename, template_text)

        if template_text == updated_text:
            logger.info(f"Job {self.job_id}: No update needed for template page {template_title}")
            file_info["steps"]["update_template"] = {"result": None, "msg": "No update needed"}
            return True

        clean_filename = cropped_filename.removeprefix('File:')
        summary = f"Update file reference to [[File:{clean_filename}]]"

        res = update_page_text(template_title, updated_text, self.site, summary=summary)
        if not res["success"]:
            error = res.get("error", "Unknown error")
            logger.warning(f"Job {self.job_id}: Failed to update template page {template_title} ({error})")
            file_info["steps"]["update_template"] = {"result": False, "msg": f"Failed to update template {template_title}"}
            return False

        file_info["steps"]["update_template"] = {"result": True, "msg": f"Updated template {template_title}"}
        return True

    # ==========================================
    # Job Lifecycle & Setup Functions
    # ==========================================

    def _initialize_job(self) -> bool:
        """Sets up job status, database hooks, and APIs."""
        try:
            jobs_service.update_job_status(self.job_id, "running", self.result_file, job_type="crop_main_files")
        except LookupError:
            logger.warning(f"Job {self.job_id}: Could not update status; job record might have been deleted.")
            return False

        self.site = get_user_site(self.user)
        if not self.site:
            logger.warning(f"Job {self.job_id}: No site authentication available")
            self._set_job_status("failed", failed_at=True)
            return False

        self.session = create_commons_session(settings.oauth.user_agent)
        return True

    def _get_templates_to_process(self) -> list[TemplateRecord]:
        """Fetches and limits the templates according to settings."""
        templates = [t for t in template_service.list_templates() if t.last_world_file]
        upload_limit = int(settings.dynamic.get("crop_newest_upload_limit", 0))
        dev_limit = settings.download.dev_limit

        if upload_limit > 0 and len(templates) > upload_limit:
            logger.info(f"Job {self.job_id}: Upload limit - limiting from {len(templates)} to {upload_limit}")
            return templates[:upload_limit]

        if dev_limit > 0 and len(templates) > dev_limit:
            logger.info(f"Job {self.job_id}: Dev mode limit - limiting from {len(templates)} to {dev_limit}")
            return templates[:dev_limit]

        return templates

    def _set_total_templates(self, total: int):
        self.result["summary"]["total"] = total
        logger.info(f"Job {self.job_id}: Found {total} templates with main files")

    def _should_cancel(self) -> bool:
        if self.cancel_event and self.cancel_event.is_set():
            logger.info(f"Job {self.job_id}: Cancellation detected, stopping.")
            self._set_job_status("cancelled", cancelled_at=True)
            return True
        return False

    def _save_progress_if_needed(self, iteration_num: int):
        if iteration_num == 1 or iteration_num % 10 == 0:
            jobs_service.save_job_result_by_name(self.result_file, self.result)

    def _log_template_processing(self, current: int, total: int, template: TemplateRecord):
        logger.info(f"Job {self.job_id}: Processing {current}/{total}: {template.title}")

    def _finalize_job(self):
        if self.result.get("status") != "cancelled":
            self._set_job_status("completed")
            logger.info(f"Job {self.job_id}: Crop processing completed")

    def _set_job_status(self, status: str, failed_at: bool = False, cancelled_at: bool = False):
        self.result["status"] = status
        if failed_at:
            self.result["failed_at"] = datetime.now().isoformat()
        if cancelled_at:
            self.result["cancelled_at"] = datetime.now().isoformat()

    # ==========================================
    # State Management & Helpers
    # ==========================================

    def _initialize_file_info(self, template: TemplateRecord) -> dict[str, Any]:
        """Creates the initial tracking dictionary for a file."""
        return {
            "template_id": template.id,
            "template_title": template.title,
            "original_file": template.last_world_file,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "cropped_filename": generate_cropped_filename(template.last_world_file),
            "error": None,
            "downloaded_path": None,
            "cropped_path": None,
            "steps": {
                "download": {"result": None, "msg": ""},
                "crop": {"result": None, "msg": ""},
                "upload_cropped": {"result": None, "msg": ""},
                "update_original": {"result": None, "msg": ""},
                "update_template": {"result": None, "msg": ""},
            },
        }

    def _fail_file(self, file_info: dict, step_name: str, error_msg: str, skip_rest: str | None = None) -> bool:
        """Marks the file as failed, sets the error, and aborts the pipeline."""
        file_info["status"] = "failed"
        file_info["error"] = error_msg
        file_info["steps"][step_name] = {"result": False, "msg": error_msg}
        if step_name in ["download", "upload_cropped"]:
            file_info["cropped_filename"] = None

        if skip_rest:
            self._mark_remaining_steps_skipped(file_info, skip_rest)

        return False

    def _skip_file(self, file_info: dict, step_name: str, reason: str) -> bool:
        """Marks the file as skipped and aborts the pipeline gracefully."""
        file_info["status"] = "skipped"
        file_info["cropped_filename"] = None
        file_info["steps"][step_name] = {"result": None, "msg": reason}
        self._mark_remaining_steps_skipped(file_info, reason)
        return False

    def _mark_remaining_steps_skipped(self, file_info: dict, reason: str):
        """Fills remaining blank steps with a skip message."""
        for step in ["upload_cropped", "update_original", "update_template"]:
            if not file_info["steps"][step]["msg"]:
                file_info["steps"][step] = {"result": None, "msg": reason}

    def _mark_as_uploaded(self, file_info: dict):
        file_info["status"] = "uploaded"

    def _update_job_summary_counters(self, file_info: dict):
        """Calculates totals for the job based on individual file outcomes."""
        self.result["files_processed"].append(file_info)

        status = file_info["status"]
        if status == "failed":
            self.result["summary"]["failed"] += 1
        elif status == "skipped":
            self.result["summary"]["skipped"] += 1
        elif status == "uploaded":
            self.result["summary"]["uploaded"] += 1

        if file_info["steps"]["download"].get("result") is True:
            self.result["summary"]["processed"] += 1

        if file_info["steps"]["crop"].get("result") is True:
            self.result["summary"]["cropped"] += 1


# Procedural wrapper to maintain compatibility with the rest of your application.
def process_crops(
    job_id: int,
    result: dict[str, Any],
    result_file: str,
    user: dict[str, Any] | None,
    cancel_event: threading.Event | None = None,
    upload_files: bool = False,
) -> dict[str, Any]:
    """
    Process cropping for all templates.
    """
    worker = CropWorker(job_id, result, result_file, user, cancel_event, upload_files)
    return worker.execute()


__all__ = [
    "process_crops",
    "CropWorker"
]
