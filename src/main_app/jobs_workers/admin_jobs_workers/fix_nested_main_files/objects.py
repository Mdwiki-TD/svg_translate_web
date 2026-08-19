"""
Objects for fix_nested_main_files worker.

"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from ...shared_objects import WorkerMapping


@dataclass
class TitleInfo:
    id: int
    title: str
    main_file: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = ""
    error: None | str = None
    message: None | str = None
    fix_result: None | dict = None
    error_type: None | str = None

    def _update(self, status: str, message: str) -> None:
        self.status = status
        self.message = message

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)  # pyright: ignore[reportCallIssue]


@dataclass
class Summary:
    total: int = 0
    processed: int = 0


@dataclass
class FixNestedMainFilesWorkerObject(WorkerMapping):
    summary: Summary = field(default_factory=Summary)
    pages_success: list[TitleInfo] = field(default_factory=list)
    pages_skipped: list[TitleInfo] = field(default_factory=list)
    pages_failed: list[TitleInfo] = field(default_factory=list)


__all__ = [
    "FixNestedMainFilesWorkerObject",
    "TitleInfo",
]
