"""Objects for crop_main_files worker."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from ...shared_objects import StandardAdminWorkerObject

logger = logging.getLogger(__name__)


@dataclass
class CropFileProcessingInfo:
    """Holds all state for a single file being processed."""

    template_id: int
    template_title: str
    original_file: str
    cropped_filename: str
    timestamp: str = ""  # Will be set in worker
    status: str = "pending"
    error: str | None = None
    downloaded_path: Optional[str] = None
    cropped_path: Optional[str] = None
    steps: dict[str, Any] = field(
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
            "downloaded_path": self.downloaded_path,
            "cropped_path": self.cropped_path,
            "steps": self.steps,
        }


@dataclass
class CropMainFilesSummary:
    total: int = 0
    processed: int = 0
    cropped: int = 0
    uploaded: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0


@dataclass
class CropMainFilesWorkerObject(StandardAdminWorkerObject):
    summary: CropMainFilesSummary = field(default_factory=CropMainFilesSummary)
    pages_uploaded: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "CropFileProcessingInfo",
    "CropMainFilesSummary",
    "CropMainFilesWorkerObject",
]
