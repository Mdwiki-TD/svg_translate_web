"""Service for managing background jobs."""

from __future__ import annotations

import functools
import json
import logging
import os
from pathlib import Path
from typing import Any

from ..config import get_settings

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def get_jobs_data_dir() -> Path:
    """Get the directory for storing job data files."""
    app_settings = get_settings()
    # Use jobs_path from settings paths
    jobs_dir = app_settings.paths.jobs_path

    if not jobs_dir:
        raise RuntimeError("jobs_path configuration is required for job result storage")

    jobs_dir = Path(jobs_dir)
    jobs_dir.mkdir(parents=True, exist_ok=True)

    return jobs_dir


class JobFilesService:
    """Manages job result files on disk."""

    def __init__(self, jobs_dir: Path | None = None) -> None:
        """Initialize with optional jobs directory.
        
        Args:
            jobs_dir: Directory for job files. Falls back to get_jobs_data_dir() if None.
        """
        self._jobs_dir = jobs_dir

    def _get_jobs_dir(self) -> Path:
        """Get the jobs directory (lazy initialization)."""
        if self._jobs_dir is None:
            self._jobs_dir = get_jobs_data_dir()
        return self._jobs_dir

    def _save_data(self, result_data: dict[str, Any], filepath: Path) -> None:
        """Save data to a JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, default=str, ensure_ascii=False)

    def save_result(self, filename: str, result_data: dict[str, Any]) -> Path:
        """Save job result to a JSON file and return the file path."""
        jobs_dir = self._get_jobs_dir()
        filepath = jobs_dir / filename
        self._save_data(result_data, filepath)
        return filepath

    def load_result(self, filename: str) -> dict[str, Any] | None:
        """Load job result from a JSON file."""
        jobs_dir = self._get_jobs_dir()
        filepath = jobs_dir / filename
        if not filepath or not os.path.exists(filepath):
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading job result from {filepath}: {e}")
            return None

    def create_cancelled_file(self, filename: str) -> Path | None:
        """Create a cancelled marker file."""
        jobs_dir = self._get_jobs_dir()
        filepath = jobs_dir / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("cancelled")
            return filepath
        except OSError:
            logger.exception(f"Error creating job cancelled file {filepath}")
            return None

    def is_cancelled_file_exist(self, filename: str) -> bool:
        """Check if a cancelled marker file exists."""
        try:
            jobs_dir = self._get_jobs_dir()
            filepath = jobs_dir / filename
            return filepath.exists()
        except OSError:
            logger.exception(f"Error checking job cancelled file {filename}")
            return False


# Module-level default instance for backward compatibility
_default_service = JobFilesService()


def save_data(result_data: dict[str, Any], filepath: Path) -> None:
    """Legacy wrapper. Use JobFilesService._save_data instead."""
    _default_service._save_data(result_data, filepath)


def save_job_result_by_name(filename: str, result_data: dict[str, Any]) -> Path:
    """Legacy wrapper. Use JobFilesService.save_result instead."""
    return _default_service.save_result(filename, result_data)


def load_job_result(filename: str) -> dict[str, Any] | None:
    """Legacy wrapper. Use JobFilesService.load_result instead."""
    return _default_service.load_result(filename)


def create_job_cancelled_file(filename: str) -> Path | None:
    """Legacy wrapper. Use JobFilesService.create_cancelled_file instead."""
    return _default_service.create_cancelled_file(filename)


def is_job_cancelled_file_exist(filename: str) -> bool:
    """Legacy wrapper. Use JobFilesService.is_cancelled_file_exist instead."""
    return _default_service.is_cancelled_file_exist(filename)


__all__ = [
    "JobFilesService",
    "get_jobs_data_dir",
    "create_job_cancelled_file",
    "is_job_cancelled_file_exist",
    "save_job_result_by_name",
    "load_job_result",
]
