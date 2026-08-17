"""Objects for crop_main_files worker."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ...shared_objects import StandardAdminWorkerObject

logger = logging.getLogger(__name__)


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
    steps: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {
            "download": {"result": None, "msg": ""},
            "crop": {"result": None, "msg": ""},
            "upload_cropped": {"result": None, "msg": ""},
            "update_original": {"result": None, "msg": ""},
            "update_template": {"result": None, "msg": ""},
            "update_page": {"result": None, "msg": ""},
            "update_cropped": {"result": None, "msg": ""},
        }
    )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for x, v in data.items():
            if isinstance(v, Path):
                data[x] = str(v)
        return data


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
    """ """

    summary: CropMainFilesSummary = field(default_factory=CropMainFilesSummary)
    pages_to_work: list[str] = field(default_factory=list)
    pages_processed: list[dict[str, Any]] = field(default_factory=list)
    pages_uploaded: list[dict[str, Any]] = field(default_factory=list)
    pages_updated: list[dict[str, Any]] = field(default_factory=list)
    pages_skipped: list[dict[str, Any]] = field(default_factory=list)
    pages_failed: list[dict[str, Any]] = field(default_factory=list)
    pages_errors: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "CropFileProcessingInfo",
    "CropMainFilesSummary",
    "CropMainFilesWorkerObject",
]
