"""Public job worker for fixing nested tags in SVG files."""

from __future__ import annotations

from .runner import fix_nested_jobs_worker_entry
from .worker import FixNestedJobsProcessor

__all__ = [
    "FixNestedJobsProcessor",
    "fix_nested_jobs_worker_entry",
]
