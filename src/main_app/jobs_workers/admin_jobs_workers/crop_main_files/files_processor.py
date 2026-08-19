"""
Worker module for cropping main files and uploading them with (cropped) suffix.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from mwclient.client import Site

from ....api_services import MwClientPage, create_commons_session
from ....config import settings
from ....database.models import TemplateRecord
from ....database.services import OwidChartsService
from ....database.templates_utils import extract_slug
from ....utils.wikitext import (
    create_cropped_file_text,
    ensure_file_prefix,
    update_original_file_text,
    update_template_page_file_reference,
)
from ....utils.wikitext.cropped_file_text.utils import update_information_author
from .objects import CropFileProcessingInfo, FileStep
from .steps import (
    crop_svg_file,
    download_file_for_cropping,
    upload_cropped_file,
)

logger = logging.getLogger(__name__)


class OneFileProcessor:

    def __init__(self, job_id: int, site: Site, args: dict[str, Any]) -> None:
        self.job_id = job_id
        self.site = site
        self.exists: dict[str, Any] = {}
        self.args = args
        self.original_dir = Path(settings.paths.crop_main_files_path) / "original"
        self.cropped_dir = Path(settings.paths.crop_main_files_path) / "cropped"
        self.session = create_commons_session(settings.other.user_agent)

        self.owid_charts_service = OwidChartsService()

    # ------------------------------------------------------------------
    # Per-template orchestration
    # ------------------------------------------------------------------

    def process_one_item(self, file_info: CropFileProcessingInfo, template: TemplateRecord) -> bool:

        cropped_filename = file_info.cropped_filename

        # pre steps if the file already in commons, skip download/upload files.
        if self._check_file_exists(cropped_filename):
            file_info.steps.download.skip("Skipped - file already exists on Commons")
            file_info.steps.crop.skip("Skipped - file already exists on Commons")
            file_info.steps.upload_cropped.skip("Skipped - file already exists on Commons")

            # Update existing page texts, including the cropped file description.
            updated = self.update_file_references(file_info, template)

            if updated:
                file_info.status = "updated"
                return True

            # if all file_info.steps "result" is None do:
            all_steps = (
                file_info.steps.update_original,
                file_info.steps.update_template,
                file_info.steps.update_page,
                file_info.steps.update_cropped,
            )
            if all(step.result is None for step in all_steps):
                file_info.status = "skipped"

            return False

        # ----------------------------------
        # Step 1 - Download
        if not self._step_download(file_info, template):
            return False

        # ----------------------------------
        # Step 2 - Crop
        cropped_output_path = self.cropped_dir / Path(cropped_filename.removeprefix("File:")).name
        if not self._step_crop(file_info, template, cropped_output_path):
            return False

        # Upload disabled → mark skipped and move on
        if self.args.get("upload_files") is False:
            file_info.status = "skipped"
            self._skip_upload_steps(file_info)
            return False

        # ----------------------------------
        # Step 3 - Upload cropped file
        up_step = self._step_upload(file_info, template)
        if up_step is False:
            return False

        elif up_step is None:
            logger.debug("file %s exists", file_info.cropped_filename)

        # Update page texts, including the cropped file description.
        updated = self.update_file_references(file_info, template)

        if up_step is True or updated:
            return True

        file_info.status = "completed"
        return False

    def update_file_references(self, file_info: CropFileProcessingInfo, template: TemplateRecord | None = None) -> bool:
        """Update original, template, content, and cropped-file page wikitext."""
        # Step 4 - Update original file wikitext
        updated = self._step_update_original(file_info)

        # Step 5 - Update template page reference
        updated2 = self._step_update_page_reference(
            file_info,
            file_info.template_title,
            file_info.steps.update_template,
        )

        # Step 6 - Update corresponding content page
        template_title = file_info.template_title
        if template_title.lower().startswith("template:"):
            updated3 = self._step_update_page_reference(
                file_info,
                template_title[9:],
                file_info.steps.update_page,
            )
        else:
            file_info.steps.update_page.skip("Skipped - title does not start with Template:")
            updated3 = False

        # Step 7 - Update the existing cropped file description with its stored OWID source citation.
        updated4 = self._step_update_cropped(file_info, template)

        return updated or updated2 or updated3 or updated4

    # ------------------------------------------------------------------
    # Individual pipeline steps
    # ------------------------------------------------------------------

    def _step_download(self, file_info: CropFileProcessingInfo, template: TemplateRecord) -> bool:
        """Download the original file. Returns True on success."""

        download_result = download_file_for_cropping(
            template.last_world_file,
            self.original_dir,
            session=self.session,
        )

        if download_result["success"]:
            downloaded_path = download_result["path"]
            file_info.steps.download.result = True
            file_info.steps.download.msg = f"Downloaded to {downloaded_path}"
            file_info.downloaded_path = downloaded_path
            return True

        error_msg = download_result.get("error", "Unknown download error")
        logger.warning("Job %s: Failed to download %s", self.job_id, template.last_world_file)

        self._fail(file_info, file_info.steps.download, error_msg)
        return False

    def _step_crop(
        self,
        file_info: CropFileProcessingInfo,
        template: TemplateRecord,
        cropped_path: Path,
    ) -> bool:
        """Crop the SVG. Returns True on success."""
        crop_result = crop_svg_file(Path(file_info.downloaded_path), cropped_path)

        if crop_result["success"]:
            file_info.steps.crop.result = True
            file_info.steps.crop.msg = f"Cropped to {cropped_path}"
            file_info.cropped_path = cropped_path
            return True

        error_msg = crop_result.get("error", "Unknown crop error")
        logger.warning("Job %s: Failed to crop %s", self.job_id, template.last_world_file)

        self._fail(file_info, file_info.steps.crop, error_msg)
        return False

    def _get_author_citation(self, template: TemplateRecord | None) -> str | None:
        """Read the OWID source citation persisted for the template's chart."""
        if template is None:
            return None

        slug = template.slug or extract_slug(template.source)
        if not slug:
            return None

        chart = self.owid_charts_service.get_chart_by_slug(slug)
        source = chart.source if chart else None
        if isinstance(source, str) and source.strip():
            return source.strip()

        logger.info("Job %s: No stored OWID author citation found for chart %s", self.job_id, slug)
        return None

    def _step_upload(self, file_info: CropFileProcessingInfo, template: TemplateRecord | None = None) -> bool | None:
        """Upload the cropped file. Returns True if upload succeeded or was skipped."""
        file_name = ensure_file_prefix(file_info.original_file)
        page = MwClientPage(file_name, self.site)
        wikitext = page.get_text()
        author_citation = self._get_author_citation(template)

        cropped_file_wikitext = create_cropped_file_text(
            file_name=file_info.original_file,
            text=wikitext,
            author_citation=author_citation,
        )

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
            file_info.steps.upload_cropped.skip("Skipped - file already exists on Commons")
            file_info.status = "skipped"

            # Still continue to wikitext updates even if file existed
            return None

        if upload_result["success"]:
            logger.info("Job %s: Successfully uploaded %s", self.job_id, file_info.cropped_filename)
            file_info.steps.upload_cropped.result = True
            file_info.steps.upload_cropped.msg = f"Uploaded as {file_info.cropped_filename}"
            file_info.status = "uploaded"

            return True

        error = upload_result.get("error", "Unknown upload error")
        logger.warning("Job %s: Failed to upload %s", self.job_id, file_info.cropped_filename)

        file_info.steps.update_original.skip("Skipped - upload failed")
        file_info.steps.update_template.skip("Skipped - upload was not successful")
        file_info.steps.update_page.skip("Skipped - upload was not successful")
        file_info.steps.update_cropped.skip("Skipped - upload was not successful")

        self._fail(file_info, file_info.steps.upload_cropped, error)
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
            file_info.steps.update_original.result = None
            file_info.steps.update_original.msg = "No update needed"
            return False

        update_result = original_page.edit(
            updated_text,
            summary="Adding/updating {{Image extracted}}",
        )

        if update_result["success"]:
            file_info.steps.update_original.result = True
            file_info.steps.update_original.msg = "Updated original file wikitext"
            file_info.steps.update_original.newrevid = update_result.get("newrevid", 0)
            return True

        error = update_result.get("error", "Unknown error")
        logger.warning(
            "Job %s: Failed to update original file text for %s (reason: %s)",
            self.job_id,
            file_info.original_file,
            error,
        )
        file_info.steps.update_original.result = False
        file_info.steps.update_original.msg = error
        return False

    def _step_update_cropped(self, file_info: CropFileProcessingInfo, template: TemplateRecord | None) -> bool:
        """Update a cropped file page's Author field from the persisted OWID source citation."""
        cropped_file_name = ensure_file_prefix(file_info.cropped_filename)
        cropped_page = MwClientPage(cropped_file_name, self.site)
        cropped_file_wikitext = cropped_page.get_text()

        if not cropped_file_wikitext:
            file_info.steps.update_cropped.result = False
            file_info.steps.update_cropped.msg = f"Empty cropped file text: {cropped_file_name}"
            return False

        author_citation = self._get_author_citation(template)
        new_wikitext = update_information_author(
            text=cropped_file_wikitext,
            author_citation=author_citation,
        )
        if new_wikitext == cropped_file_wikitext:
            logger.info("Job %s: No cropped file update needed for %s", self.job_id, cropped_file_name)
            file_info.steps.update_cropped.result = None
            file_info.steps.update_cropped.msg = "No update needed"
            return False

        update_result = cropped_page.edit(
            new_wikitext,
            summary="Update cropped file author attribution from OWID source",
        )
        if update_result.get("success"):
            file_info.steps.update_cropped.result = True
            file_info.steps.update_cropped.msg = "Updated cropped file wikitext"
            file_info.steps.update_cropped.newrevid = update_result.get("newrevid", 0)
            return True

        error = update_result.get("error", "Unknown error")
        logger.warning(
            "Job %s: Failed to update cropped file text for %s (reason: %s)",
            self.job_id,
            cropped_file_name,
            error,
        )
        file_info.steps.update_cropped.result = False
        file_info.steps.update_cropped.msg = error
        return False

    def _step_update_page_reference(
        self,
        file_info: CropFileProcessingInfo,
        page_title: str,
        step_obj: FileStep,
    ) -> bool:
        """Update a page to reference the cropped file."""

        page = MwClientPage(page_title, self.site)

        if not page.exists():
            logger.warning("Job %s: Page does not exist: %s", self.job_id, page_title)
            step_obj.result = None
            step_obj.msg = f"Page does not exist: {page_title}"
            return False

        page_text = page.get_text()

        if not page_text:
            logger.warning("Job %s: Empty page text for %s", self.job_id, page_title)
            step_obj.result = False
            step_obj.msg = f"Empty page text: {page_title}"
            return False

        updated_text = update_template_page_file_reference(
            file_info.original_file,
            file_info.cropped_filename,
            page_text,
        )

        if page_text == updated_text:
            logger.info("Job %s: No update needed for page %s", self.job_id, page_title)
            step_obj.result = None
            step_obj.msg = "No update needed"
            return False

        summary = f"Update file reference to [[File:{file_info.cropped_filename.removeprefix('File:')}]]"

        update_result = page.edit(updated_text, summary)

        if update_result.get("success"):
            step_obj.result = True
            step_obj.msg = f"Updated page {page_title}"
            step_obj.newrevid = update_result.get("newrevid", 0)
            return True

        error = update_result.get("error", "Unknown error")

        logger.warning("Job %s: Failed to update page %s (reason: %s)", self.job_id, page_title, error)

        step_obj.result = False
        step_obj.msg = f"Failed to update page {page_title}: {error}"

        return False

    def _check_file_exists(self, cropped_filename):
        file_exists = self.exists.get(cropped_filename.removeprefix("File:"))
        if file_exists is None:
            file_exists = MwClientPage(cropped_filename, self.site).exists()
        return file_exists

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _skip_upload_steps(self, file_info: CropFileProcessingInfo) -> None:
        file_info.steps.upload_cropped.skip("Skipped - upload disabled")
        file_info.steps.update_original.skip("Skipped - upload disabled")
        file_info.steps.update_template.skip("Skipped - upload disabled")
        file_info.steps.update_page.skip("Skipped - upload disabled")
        file_info.steps.update_cropped.skip("Skipped - upload disabled")
        logger.info("Job %s: Skipped upload for %s (upload disabled)", self.job_id, file_info.cropped_filename)
        file_info.cropped_filename = ""
        file_info.status = "skipped"

    def _fail(self, info: CropFileProcessingInfo, step_obj: FileStep, error: str) -> None:
        """Mark a step and the info as failed."""
        step_obj.result = False
        step_obj.msg = error
        info.status = "failed"
        info.error = error


__all__ = [
    "OneFileProcessor",
]
