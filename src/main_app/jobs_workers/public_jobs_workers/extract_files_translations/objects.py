"""
Objects for copy_svg_langs worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ...shared_objects import StandardAdminSummary, WorkerObject


@dataclass
class StageDetail:
    name: str = ""
    status: str = "pending"
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
    processfiles: StageDetail = field(
        default_factory=lambda: StageDetail(
            name="processfiles",
            message="process Files",
        )
    )


@dataclass
class StepResult:
    result: bool | None = None
    msg: str = ""
    details: dict[str, Any] | None = None

    def _update(self, result: bool | None | str = "z", msg: str = "", details: dict[str, Any] | None = None) -> None:

        if result is None or isinstance(result, bool):
            self.result = result

        if msg:
            self.msg = msg

        if details:
            self.details = details


@dataclass
class FileSteps:
    download: StepResult = field(default_factory=lambda: StepResult())
    load_mapping: StepResult = field(default_factory=lambda: StepResult())
    languages: StepResult = field(default_factory=lambda: StepResult())


@dataclass
class FilesProcessedItem:
    title: str
    file_path: str | None = None
    status: str = "pending"
    error: str | None = None
    steps: FileSteps = field(default_factory=lambda: FileSteps())
    is_mapping_merged: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)  # pyright: ignore[reportCallIssue]


@dataclass
class ExtractFilesTranslationsObject(WorkerObject):

    summary: StandardAdminSummary = field(default_factory=StandardAdminSummary)
    title: str | None = None

    stages: Stages = field(default_factory=Stages)
    mapping: dict[str, Any] = field(default_factory=dict)
    languages: list[str] = field(default_factory=list)

    files_processed: list[FilesProcessedItem] = field(default_factory=list)
    files_success: list[FilesProcessedItem] = field(default_factory=list)
    files_failed: list[FilesProcessedItem] = field(default_factory=list)

    mapping_mereged: int = 0
    note: str = ""

    def to_json(self) -> dict[str, Any]:
        """
        Converts the dataclass instance back to its original dictionary format.
        """

        return asdict(self)  # pyright: ignore[reportCallIssue]


__all__ = [
    "StepResult",
    "FilesProcessedItem",
    "ExtractFilesTranslationsObject",
]
