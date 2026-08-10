"""
Worker module for extract_files_translations.
"""

from __future__ import annotations

import logging

from ...objects import JobsRunner
from .worker import ExtractFilesTranslationsWorker

logger = logging.getLogger(__name__)


def extract_files_translations_worker_entry(data: JobsRunner) -> None:
    """Entry point for the background job."""

    worker = ExtractFilesTranslationsWorker(data)
    worker.run()


__all__ = [
    "extract_files_translations_worker_entry",
]
