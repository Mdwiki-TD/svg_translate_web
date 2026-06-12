""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ...base_worker_object import WorkerObject

logger = logging.getLogger(__name__)


StepResult = dict[str, Any]


@dataclass
class CropFileProcessingInfo:
    """Holds all state for a single file being processed."""

    template_id: int
    template_title: str
    original_file: str
    cropped_filename: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"
    error: str | None = None
    downloaded_path: Path | None = None
    cropped_path: Path | None = None
    steps: dict[str, StepResult] = field(
        default_factory=lambda: {
            "download": {"result": None, "msg": ""},
            "crop": {"result": None, "msg": ""},
            "upload_cropped": {"result": None, "msg": ""},
            "update_original": {"result": None, "msg": ""},
            "update_template": {"result": None, "msg": ""},
            "update_page": {"result": None, "msg": ""},
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "template_title": self.template_title,
            "original_file": self.original_file,
            "cropped_filename": self.cropped_filename,
            "timestamp": self.timestamp,
            "status": self.status,
            "error": self.error,
            "downloaded_path": str(self.downloaded_path) if self.downloaded_path else None,
            "cropped_path": str(self.cropped_path) if self.cropped_path else None,
            "steps": self.steps,
        }


@dataclass
class CropSummary:
    total: int = 0
    processed: int = 0

    cropped: int = 0
    uploaded: int = 0
    updated: int = 0

    skipped: int = 0
    failed: int = 0


@dataclass
class CropMainFilesWorkerObject(WorkerObject):
    """
    "note": "",
    "status": "pending",
    "errors": [],
    "args": {},
    "job_id": self.job_id,
    "started_at": datetime.now().isoformat(),
    "completed_at": None,
    "cancelled_at": None,
    "pages_processed": [],
    "pages_uploaded": [],
    "pages_updated": [],
    "pages_skipped": [],
    "pages_failed": [],
    """

    summary: CropSummary = field(default_factory=CropSummary)
    pages_to_work: list[str] = field(default_factory=list)
    pages_processed: list[dict[str, Any]] = field(default_factory=list)
    pages_errors: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "CropSummary",
    "CropMainFilesWorkerObject",
]
