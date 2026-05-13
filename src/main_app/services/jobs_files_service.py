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
    # Use svg_jobs_path from settings paths
    jobs_dir = getattr(settings.paths, "svg_jobs_path", None)
    if not jobs_dir:
        raise RuntimeError("MAIN_DIR/svg_jobs environment variable is required for job result storage")
    jobs_dir = Path(jobs_dir)
    jobs_dir.mkdir(parents=True, exist_ok=True)
    return jobs_dir


def save_job_result_by_name(filename: str, result_data: Dict[str, Any]) -> Path:
    """Save job result to a JSON file and return the file path."""
    jobs_dir = get_jobs_data_dir()
    # Use microseconds to avoid race conditions if multiple jobs complete simultaneously
    filepath = jobs_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, default=str, ensure_ascii=False)

    return filepath


def save_job_result(job_id: int, result_data: Dict[str, Any]) -> str:
    """Save job result to a JSON file and return the file path."""
    jobs_dir = get_jobs_data_dir()
    # Use microseconds to avoid race conditions if multiple jobs complete simultaneously
    filename = f"job_{job_id}.json"
    filepath = jobs_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2, default=str, ensure_ascii=False)

    return str(filepath.name)


def load_job_result(result_file: str) -> Dict[str, Any] | None:
    """Load job result from a JSON file."""
    jobs_dir = get_jobs_data_dir()
    result_file = jobs_dir / result_file
    if not result_file or not os.path.exists(result_file):
        return None

    try:
        with open(result_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading job result from {result_file}: {e}")
        return None


__all__ = [
    "get_jobs_data_dir",
    "save_job_result_by_name",
    "save_job_result",
    "load_job_result",
]
