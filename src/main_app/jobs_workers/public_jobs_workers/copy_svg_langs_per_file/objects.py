"""
Objects for copy_svg_langs_per_file worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class StageDetail:
    name: str = ""
    status: str = "Pending"
    message: str = ""
    data: Any = None


@dataclass
class Stages:
    text: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="text",
            message="Getting text",
        )
    )
    titles: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="titles",
            message="Getting titles",
        )
    )
    translations: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="translations",
            message="Getting translations",
        )
    )
    processfiles: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="processfiles",
            message="process Files",
        )
    )


@dataclass
class StepResult:
    result: Optional[bool] = None
    msg: str = ""
    details: Optional[dict[str, Any]] = None


@dataclass
class FileSteps:
    download: StepResult = field(default_factory=lambda: StepResult())
    nested: StepResult = field(default_factory=lambda: StepResult())
    inject: StepResult = field(default_factory=lambda: StepResult())
    upload: StepResult = field(default_factory=lambda: StepResult())


@dataclass
class FilesProcessedItem:
    title: str
    file_path: Optional[str] = None
    status: str = "pending"
    error: Optional[str] = None
    steps: FileSteps = field(default_factory=lambda: FileSteps())


@dataclass
class CopySvgLangsPerFileWorkerObject(StandardAdminWorkerObject):
    title: Optional[str] = None
    stages: Stages = field(default_factory=Stages)
    files_processed: list[FilesProcessedItem] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        """
        Converts the dataclass instance back to its original dictionary format.
        """

        return asdict(self)


__all__ = [
    "StepResult",
    "FileSteps",
    "FilesProcessedItem",
    "CopySvgLangsPerFileWorkerObject",
]
