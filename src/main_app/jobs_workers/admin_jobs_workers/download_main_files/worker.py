"""
Worker module for downloading main files from remote source to local filesystem.
"""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path

import requests

from ....api_services import FilesService, create_commons_session
from ....api_services.files_service import DownloadAndSaveData
from ....config import settings
from ....database.models import TemplateRecord
from ....database.services import TemplateService
from ...base_worker import BaseObjectsJobWorker
from ...objects import JobsRunner
from .objects import DownloadMainFilesWorkerObject, FileInfo

logger = logging.getLogger(__name__)


def generate_main_files_zip(main_files_zip_name) -> Path:
    """
    Generate a zip archive of all files in the main_files_path directory.

    Creates the zip file on disk in the main_files_path directory.
    Only includes actual files (not directories), excluding the zip file itself.

    Returns:
        Path: Path to the created zip file

    Raises:
        FileNotFoundError: If main_files_path directory does not exist
        RuntimeError: If no files are found to zip
    """
    main_files_path = Path(settings.paths.main_files_path)

    if not main_files_path.exists():
        raise FileNotFoundError(f"Main files directory does not exist: {main_files_path}")

    zip_file_path = main_files_path / main_files_zip_name

    # Create the zip file
    file_count = 0
    with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in main_files_path.iterdir():
            if file_path.is_file() and file_path.name != main_files_zip_name:
                zip_file.write(file_path, file_path.name)
                file_count += 1

    if file_count == 0:
        # Remove empty zip file and raise error
        zip_file_path.unlink(missing_ok=True)
        raise RuntimeError("No files found to zip in main_files_path")

    logger.info("Generated %s with %d files", zip_file_path, file_count)
    return zip_file_path


class DownloadMainFilesWorker(BaseObjectsJobWorker):
    """Worker for downloading main files from Commons to local filesystem."""

    def __init__(self, data: JobsRunner) -> None:
        self.output_dir = Path(settings.paths.main_files_path)
        super().__init__(data)
        self.args = data.args or {}

        self.result: DownloadMainFilesWorkerObject = DownloadMainFilesWorkerObject(
            job_id=self.job_id,
            args=self.args,
            output_path=str(self.output_dir),
        )

        self.session: requests.Session | None = None
        self.main_files_zip_name = self.args.get("main_files_zip_name", "main_files.zip")
        self.limit_items = self.args.get("limit_items") or 0
        self.files_service = FilesService()

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "download_main_files"

    def _apply_limits(self, templates_with_files: list[TemplateRecord]) -> list[TemplateRecord]:
        _limit = self.limit_items if isinstance(self.limit_items, int) else 0
        if _limit > 0 and len(templates_with_files) > _limit:
            logger.info("Job %s: limiting from %d to %d page", self.job_id, len(templates_with_files), _limit)
            return templates_with_files[:_limit]
        return templates_with_files

    def _load_templates(self) -> list[TemplateRecord]:
        # Get all templates with main files
        templates = TemplateService().list()
        templates_with_files = [t for t in templates if t.main_file]
        return self._apply_limits(templates_with_files)

    def _process_one_item(self, file_info: FileInfo) -> bool:
        try:
            file_data: DownloadAndSaveData = self.files_service.download_and_save(
                title=file_info.filename,
                out_dir=self.output_dir,
                overwrite_download=True,
            )
        except Exception as e:
            file_info.status = "failed"
            file_info.error = f"Exception: {str(e)}"
            file_info.error_type = type(e).__name__
            logger.exception("Job %s: Error processing %s", self.job_id, file_info.template_title)
            return False

        # =================
        if file_data.result == "success":
            file_info.status = "downloaded"
            file_info.path = file_data.path
            file_info.size_bytes = file_data.size_bytes
            return True

        file_info.status = "failed"
        file_info.error = file_data.error
        logger.warning("Job %s: Failed to download %s: %s", self.job_id, file_info.filename, file_data.error)

        return False

    def process(self) -> DownloadMainFilesWorkerObject:
        """Execute the download processing logic."""
        if not self._check_site():
            return self.result

        templates_with_files = self._load_templates()

        self.result.summary.total = len(templates_with_files)
        self.result.output_path = str(self.output_dir)

        logger.info("Job %s: Found %d templates with main files", self.job_id, len(templates_with_files))

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create a services session for all downloads
        self.session = create_commons_session(settings.other.user_agent)

        per_item = self.get_priority(len(templates_with_files))

        for n, template in enumerate(templates_with_files, start=1):
            logger.info("Job %s: Processing %d/%d: %s", self.job_id, n, len(templates_with_files), template.title)

            # Check for cancellation
            if self.is_cancelled():
                logger.info("Job %s: Cancellation detected, stopping.", self.job_id)
                break

            file_info = FileInfo.from_template(template)

            ok = self._process_one_item(file_info)

            self.update_status(file_info)

            if ok and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            # Save progress periodically
            if n == 1 or n % per_item == 0:
                self._save_progress()

        # Generate zip file after successful completion
        if self.result.status != "cancelled":
            try:
                generate_main_files_zip(self.main_files_zip_name)
                logger.info("Job %s: Generated main_files.zip successfully", self.job_id)
            except Exception as e:
                logger.exception("Job %s: Failed to generate main_files.zip: %s", self.job_id, e)

        logger.info(
            "Job %s completed: %d success, %d failed",
            self.job_id,
            self.result.summary.success,
            self.result.summary.failed,
        )

        return self.result

    def update_status(self, info: FileInfo):
        self.result.summary.processed += 1

        if info.status.lower() in ["pending", "running"]:
            info.status = "completed"

        if info.status == "downloaded":
            self.result.files_downloaded.append(info)
            self.result.summary.success += 1

        elif info.status == "failed":
            self.result.files_failed.append(info)
            self.result.summary.failed += 1
        else:
            self.result.files_processed.append(info)


__all__ = [
    "DownloadMainFilesWorker",
]
