"""
Objects for fix_nested_main_files worker.

"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from ....database.models import TemplateRecord
from ...shared_objects import STATUS_LITERAL, WorkerMapping


@dataclass
class TitleInfo:
    id: int
    main_file: str
    title: str = ""
    status: STATUS_LITERAL = "pending"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    error: None | str = None
    message: None | str = None
    fix_result: None | dict = None
    error_type: None | str = None

    def _update(self, status: STATUS_LITERAL, message: str) -> None:
        self.status = status
        self.message = message

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_template(cls, template: TemplateRecord) -> TitleInfo:
        return cls(
            id=template.id,
            title=template.title,
            main_file=template.main_file,
            timestamp=datetime.now().isoformat(),
        )


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
