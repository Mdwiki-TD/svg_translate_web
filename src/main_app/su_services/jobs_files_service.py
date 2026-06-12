"""Service for managing background jobs."""

from __future__ import annotations

import functools
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from ..config import settings

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def get_jobs_data_dir() -> Path:
    """Get the directory for storing job data files."""
    # Use jobs_path from settings paths
    jobs_dir = getattr(settings.paths, "jobs_path", None)
    if not jobs_dir:
        raise RuntimeError("jobs_path configuration is required for job result storage")
    jobs_dir = Path(jobs_dir)
    jobs_dir.mkdir(parents=True, exist_ok=True)
    return jobs_dir


def save_data(result_data, filepath) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, default=str, ensure_ascii=False)


def save_job_result_by_name(filename: str, result_data: Dict[str, Any]) -> Path:
    """Save job result to a JSON file and return the file path."""
    jobs_dir: Path = get_jobs_data_dir()
    # Use microseconds to avoid race conditions if multiple jobs complete simultaneously
    filepath = jobs_dir / filename

    save_data(result_data, filepath)
    return filepath


def load_job_result(result_file: str) -> Dict[str, Any] | None:
    """Load job result from a JSON file."""
    jobs_dir: Path = get_jobs_data_dir()
    result_file = jobs_dir / result_file  # type: ignore
    if not result_file or not os.path.exists(result_file):
        return None

    try:
        with open(result_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading job result from {result_file}: {e}")
        return None


def create_job_cancelled_file(filename: str) -> Path | None:
    jobs_dir: Path = get_jobs_data_dir()
    filepath = jobs_dir / filename
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("cancelled")
        return filepath
    except OSError:
        logger.exception(f"Error creating job cancelled file {filepath}")
        return None


def is_job_cancelled_file_exist(filename: str) -> bool:
    try:
        jobs_dir: Path = get_jobs_data_dir()
        filepath = jobs_dir / filename

        return filepath.exists()
    except OSError:
        logger.exception(f"Error checking job cancelled file {filename}")
        return False


__all__ = [
    "get_jobs_data_dir",
    "create_job_cancelled_file",
    "is_job_cancelled_file_exist",
    "save_job_result_by_name",
    "load_job_result",
]
