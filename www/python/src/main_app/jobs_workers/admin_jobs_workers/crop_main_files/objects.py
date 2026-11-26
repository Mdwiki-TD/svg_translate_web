"""Objects for crop_main_files worker."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from ....database.models import TemplateRecord
from ....jobs.shared_objects import STATUS_LITERAL, SharedMapToJson, SharedworkerObject

logger = logging.getLogger(__name__)


@dataclass
class FileStep(SharedMapToJson):
    result: Any = None
    msg: str = ""
    newrevid: int | None = None

    def skip(self, msg: str) -> None:
        self.result = None
        self.msg = msg


@dataclass
class CropFileSteps(SharedMapToJson):
    download: FileStep = field(default_factory=FileStep)
    crop: FileStep = field(default_factory=FileStep)
    upload_cropped: FileStep = field(default_factory=FileStep)
    update_original: FileStep = field(default_factory=FileStep)
    update_template: FileStep = field(default_factory=FileStep)
    update_page: FileStep = field(default_factory=FileStep)
    update_cropped: FileStep = field(default_factory=FileStep)


@dataclass
class CropFileProcessingInfo(SharedMapToJson):
    """Holds all state for a single file being processed."""

    template_id: int
    template_title: str
    original_file: str
    cropped_filename: str
    status: STATUS_LITERAL = "pending"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error: str | None = None
    downloaded_path: Path | None = None
    cropped_path: Path | None = None
    steps: CropFileSteps = field(default_factory=CropFileSteps)

    @classmethod
    def from_template(cls, template: TemplateRecord) -> CropFileProcessingInfo:
        cropped_filename = cls.generate_cropped_filename(
            template.last_world_file,  # pyright: ignore[reportArgumentType]
        )

        return cls(
            template_id=template.id,
            template_title=template.title,
            original_file=template.last_world_file,  # pyright: ignore[reportArgumentType]
            cropped_filename=cropped_filename,
            timestamp=datetime.now().isoformat(),
        )

    @staticmethod
    def generate_cropped_filename(filename: str) -> str:
        """
        Transform filename to cropped version.

        Examples:
            "File:Death rate from obesity, World, 2021.svg"
            → "File:Death rate from obesity, World, 2021 (cropped).svg"
        """
        if not filename:
            return filename

        if filename.startswith("File:"):
            base_name = filename[5:]
        else:
            base_name = filename

        path = Path(base_name)
        new_stem = f"{path.stem} (cropped)"
        new_filename = new_stem + path.suffix
        return f"File:{new_filename}"


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
class CropMainFilesWorkerObject(SharedworkerObject):
    """ """

    summary: CropMainFilesSummary = field(default_factory=CropMainFilesSummary)
    pages_to_work: list[str] = field(default_factory=list)
    pages_processed: list[CropFileProcessingInfo] = field(default_factory=list)
    pages_uploaded: list[CropFileProcessingInfo] = field(default_factory=list)
    pages_updated: list[CropFileProcessingInfo] = field(default_factory=list)
    pages_skipped: list[CropFileProcessingInfo] = field(default_factory=list)
    pages_failed: list[CropFileProcessingInfo] = field(default_factory=list)


__all__ = [
    "FileStep",
    "CropFileSteps",
    "CropFileProcessingInfo",
    "CropMainFilesSummary",
    "CropMainFilesWorkerObject",
]
