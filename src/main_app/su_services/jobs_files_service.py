"""Service for managing background jobs."""

from __future__ import annotations

import functools
import json
import logging
from pathlib import Path
from typing import Any

from ..config import settings

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def get_jobs_data_dir() -> Path:
    """Get the directory for storing job data files."""
    jobs_dir = getattr(settings.paths, "jobs_path", None)
    if not jobs_dir:
        raise RuntimeError("jobs_path configuration is required for job result storage")
    jobs_dir = Path(jobs_dir)
    jobs_dir.mkdir(parents=True, exist_ok=True)
    return jobs_dir


def _safe_job_path(filename: str) -> Path:
    """Resolve a job file path and verify it stays within the jobs directory.

    Args:
        filename: The job file name (may contain relative path segments).

    Returns:
        The resolved, validated absolute Path.

    Raises:
        ValueError: If the resolved path escapes the jobs directory.
    """
    jobs_dir = get_jobs_data_dir()
    candidate = (jobs_dir / filename).resolve()
    if jobs_dir not in candidate.parents and candidate != jobs_dir:
        raise ValueError(f"Path traversal blocked: {candidate}")
    return candidate


def save_data(result_data: dict[str, Any], filepath: Path) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, default=str, ensure_ascii=False)


def save_job_result_by_name(filename: str, result_data: dict[str, Any]) -> Path:
    """Save job result to a JSON file and return the file path."""
    filepath = _safe_job_path(filename)
    save_data(result_data, filepath)
    return filepath


def load_job_result(result_file: str) -> dict[str, Any] | None:
    """Load job result from a JSON file."""
    try:
        result_file_path = _safe_job_path(result_file)
    except ValueError:
        logger.warning("Invalid job result file path: %s", result_file)
        return None

    if not result_file_path.exists():
        return None

    try:
        with open(result_file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        logger.exception("Error loading job result from %s", result_file_path)
        return None


def create_job_cancelled_file(filename: str) -> Path | None:
    try:
        filepath = _safe_job_path(filename)
    except ValueError:
        logger.warning("Invalid job cancelled file path: %s", filename)
        return None

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("cancelled")
        return filepath
    except OSError:
        logger.exception("Error creating job cancelled file %s", filepath)
        return None


def is_job_cancelled_file_exist(filename: str) -> bool:
    try:
        filepath = _safe_job_path(filename)
    except ValueError:
        return False

    try:
        return filepath.exists()
    except OSError:
        logger.exception("Error checking job cancelled file %s", filename)
        return False


__all__ = [
    "get_jobs_data_dir",
    "create_job_cancelled_file",
    "is_job_cancelled_file_exist",
    "save_job_result_by_name",
    "load_job_result",
]
