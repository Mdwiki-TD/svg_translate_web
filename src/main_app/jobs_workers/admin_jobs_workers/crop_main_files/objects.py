"""
{
            "note": "",
            "status": "pending",
            "errors": [],
            "args": {},
            "job_id": self.job_id,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "total": 0,
                "processed": 0,
                "cropped": 0,
                "uploaded": 0,
                "updated": 0,
                "skipped": 0,
                "failed": 0,
            },
            "pages_processed": [],
            "pages_uploaded": [],
            "pages_updated": [],
            "pages_skipped": [],
            "pages_failed": [],
        }
        """

from __future__ import annotations

from datetime import datetime
import logging
from dataclasses import dataclass, field
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
class RedirectsSummary:
    scanned: int = 0
    total: int = 0

    created: int = 0
    errors: int = 0
    skipped: int = 0

    already_exists: int = 0
    target_missing: int = 0


@dataclass
class CreateRedirectsWorkerObject(WorkerObject):
    summary: RedirectsSummary = field(default_factory=RedirectsSummary)
    pages_to_work: list[str] = field(default_factory=list)
    pages_processed: list[dict[str, Any]] = field(default_factory=list)
    pages_errors: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "RedirectsSummary",
    "CreateRedirectsWorkerObject",
]
