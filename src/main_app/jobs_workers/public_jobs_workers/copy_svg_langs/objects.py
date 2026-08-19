"""
Objects for copy_svg_langs worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ...shared_objects import STATUS_LITERAL, StandardAdminSummary, WorkerMapping


@dataclass
class SvgLangsConfig:
    upload: bool | None
    upload_files: bool | None
    upload_limit: int = 0
    limit_items: int = 0
    overwrite_translations: bool = True
    overwrite_download: bool = True
    output_dir: Path | None = None
    output_dir_files: Path | None = None

    # --- Mapping ---
    merge_mapping_all_files: bool = False
    """ merge mapping for all files not only the main_file """


@dataclass
class StageDetail:
    name: str = ""
    status: STATUS_LITERAL = "pending"
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
    result: bool | None = None
    msg: str = ""
    details: dict[str, Any] | None = None

    def _update(self, result: bool | None = None, msg: str = "", details: dict[str, Any] | None = None) -> None:
        self.result = result

        if msg:
            self.msg = msg

        if details:
            self.details = details


@dataclass
class FileSteps:
    download: StepResult = field(default_factory=lambda: StepResult())
    nested: StepResult = field(default_factory=lambda: StepResult())
    translations: StepResult = field(
        default_factory=lambda: StepResult(msg="", details={"new": 0, "updated": 0, "inserted": 0, "new_list": []})
    )
    inject: StepResult = field(default_factory=lambda: StepResult())
    upload: StepResult = field(default_factory=lambda: StepResult())


@dataclass
class FilesProcessedItem:
    title: str
    file_path: str | None = None
    status: STATUS_LITERAL = "pending"
    error: str | None = None
    steps: FileSteps = field(default_factory=lambda: FileSteps())
    is_mapping_merged: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)  # pyright: ignore[reportCallIssue]


@dataclass
class CopySvgLangsWorkerObject(WorkerMapping):

    summary: StandardAdminSummary = field(default_factory=StandardAdminSummary)
    title: str | None = None
    main_title: str | None = None

    stages: Stages = field(default_factory=Stages)
    translations: list[dict[str, str]] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)

    files_processed: list[FilesProcessedItem] = field(default_factory=list)
    files_success: list[FilesProcessedItem] = field(default_factory=list)
    files_skipped: list[FilesProcessedItem] = field(default_factory=list)
    files_failed: list[FilesProcessedItem] = field(default_factory=list)

    mapping_mereged: int = 0
    note: str = ""

    def to_json(self) -> dict[str, Any]:
        """
        Converts the dataclass instance back to its original dictionary format.
        """

        return asdict(self)  # pyright: ignore[reportCallIssue]


__all__ = [
    "SvgLangsConfig",
    "StepResult",
    "FileSteps",
    "FilesProcessedItem",
    "CopySvgLangsWorkerObject",
]
