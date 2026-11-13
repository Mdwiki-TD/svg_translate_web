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

from ..config import get_settings

logger = logging.getLogger(__name__)


class JobFilesService:
    """Manage job result files and cancellation markers on disk.

    The base directory is resolved from application settings and can be
    overridden for testing.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = base_dir

    @property
    def jobs_dir(self) -> Path:
        """Resolve and cache the jobs data directory."""
        if self._base_dir is not None:
            return self._base_dir
        app_settings = get_settings()
        # Use jobs_path from settings paths
        jobs_dir = app_settings.paths.jobs_path

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


svc = JobFilesService()
save_data = svc._save_data
save_job_result_by_name = svc.save_result
load_job_result = svc.load_result
create_cancel_file = svc.create_cancel_file
is_cancel_file_exist = svc.is_cancel_file_exist

__all__ = [
    "JobFilesService",
    "get_jobs_data_dir",
    "create_cancel_file",
    "is_cancel_file_exist",
    "save_job_result_by_name",
    "load_job_result",
]
