"""Service for managing background job result files.

Provides :class:`JobFilesService` for saving and loading job result JSON files
and cancellation markers, plus backward-compatible legacy functions.
"""

from __future__ import annotations

import functools
import json
import logging
import os
from pathlib import Path
from typing import Any

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


class JobFilesService:
    """Manage job result files and cancellation markers on disk.

    The base directory is resolved from application settings and can be
    overridden for testing.
    """

    def __init__(
        self,
        base_dir: Path | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.jobs_dir = base_dir or self._load_jobs_dir()

    def _load_jobs_dir(self) -> Path:
        """Resolve and cache the jobs data directory."""
        # Use jobs_path from settings paths
        jobs_dir = self.settings.paths.jobs_path

        if not jobs_dir:
            raise RuntimeError("jobs_path configuration is required for job result storage")

        path = Path(jobs_dir)
        path.mkdir(parents=True, exist_ok=True)

        return path

    @staticmethod
    def _save_data(result_data: dict[str, Any], filepath: Path) -> None:
        """Write *result_data* as JSON to *filepath*."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, default=str, ensure_ascii=False)

    def save_result(self, filename: str, result_data: dict[str, Any]) -> Path:
        """Save job result to a JSON file and return the file path."""
        # Use microseconds to avoid race conditions if multiple jobs complete simultaneously
        filepath = self.jobs_dir / filename
        self._save_data(result_data, filepath)
        return filepath

    def _load_result(self, filename: str) -> dict[str, Any] | None:
        """Load job result from a JSON file."""
        filepath = self.jobs_dir / filename
        if not filepath or not os.path.exists(filepath):
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading job result from {filename}: {e}")
            return None

    def load_result(self, filename: str) -> dict[str, Any] | None:
        """Load job result from a JSON file."""
        data = self._load_result(filename)
        if data is not None:
            # replace pages_errors with pages_failed
            if "pages_errors" in data:
                data["pages_failed"] = data.pop("pages_errors")

            # replace pages_changed with pages_updated
            if "pages_changed" in data:
                data["pages_updated"] = data.pop("pages_changed")

        return data

    @staticmethod
    def payload_file_name(job_id: int, job_type: str) -> str:
        """Return the durable payload file name of a queued job."""
        return f"{job_type}_job_{job_id}.payload.json"

    def save_payload(self, job_id: int, job_type: str, payload: dict[str, Any]) -> Path:
        """Persist the execution payload of a queued job.

        A queued job may wait for a long time and can be dispatched by another
        process, so its payload must survive web restarts. Only non-sensitive
        data belongs here (args, sanitized form_data, username); never OAuth
        tokens or secrets.

        Args:
            job_id: The job record id.
            job_type: The job type, used to build the file name.
            payload: JSON serializable execution data.

        Returns:
            The path of the written payload file.
        """
        filename = self.payload_file_name(job_id, job_type)
        return self.save_result(filename, payload)

    def load_payload(self, job_id: int, job_type: str) -> dict[str, Any] | None:
        """Load the persisted execution payload of a job, or None if missing."""
        filename = self.payload_file_name(job_id, job_type)
        data = self._load_result(filename)
        return data if isinstance(data, dict) else None

    def delete_payload(self, job_id: int, job_type: str) -> bool:
        """Remove the persisted payload file of a job.

        Args:
            job_id: The job record id.
            job_type: The job type, used to build the file name.

        Returns:
            True when a payload file was removed.
        """
        filepath = self.jobs_dir / self.payload_file_name(job_id, job_type)
        try:
            filepath.unlink(missing_ok=True)
            return True
        except OSError:
            logger.exception("Error deleting job payload file %s", filepath)
            return False

    def create_cancel_file(self, filename: str) -> Path | None:
        """Create a cancellation marker file."""
        filepath = self.jobs_dir / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("cancelled")
            return filepath
        except OSError:
            logger.exception(f"Error creating job cancelled file {filepath}")
            return None

    def is_cancel_file_exist(self, filename: str) -> bool:
        """Check whether a cancellation marker file exists."""
        try:
            filepath = self.jobs_dir / filename
            return filepath.exists()
        except OSError:
            logger.exception(f"Error checking job cancelled file {filename}")
            return False


@functools.lru_cache(maxsize=1)
def get_jobs_data_dir() -> Path:
    """Legacy entry point. Returns the jobs data directory path."""
    return JobFilesService().jobs_dir


__all__ = [
    "JobFilesService",
    "get_jobs_data_dir",
]
