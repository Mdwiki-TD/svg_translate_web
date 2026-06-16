"""
Objects for copy_svg_langs_per_file worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from ...shared_objects import StandardAdminWorkerObject

@dataclass
class StepResult:
    result: Optional[bool] = None
    msg: str = ""


@dataclass
class FileSteps:
    download: StepResult = field(default_factory=lambda: StepResult())
    nested: StepResult = field(default_factory=lambda: StepResult())
    inject: StepResult = field(default_factory=lambda: StepResult())
    upload: StepResult = field(default_factory=lambda: StepResult())


@dataclass
class FilesProcessedItem:
    title: str
    status: str = "pending"
    error: Optional[str] = None
    steps: FileSteps = field(default_factory=lambda: FileSteps())


@dataclass
class CopySvgLangsPerFileWorkerObject(StandardAdminWorkerObject):
    job_id: Optional[int] = None
    note: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    summary: dict[str, Any] = field(default_factory=dict)
    title: Optional[str] = None
    results_summary: dict[str, Any] = field(default_factory=dict)
    files_processed: dict[str, FilesProcessedItem] = field(default_factory=dict)

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
