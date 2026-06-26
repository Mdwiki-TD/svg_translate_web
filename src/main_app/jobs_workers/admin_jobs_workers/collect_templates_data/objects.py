"""
Objects for collect_templates_data worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class StepResult:
    """
    "main_file": {"result": None, "value": "", "new_value": "", "msg": ""},
    """

    result: Optional[bool | str] = None
    value: str = ""
    new_value: str = ""
    msg: str = ""

    def _update(self, result: str = "", msg: str = "", new_value: str = "") -> None:
        if result:
            self.result = result

        if msg:
            self.msg = msg

        if new_value:
            self.new_value = new_value


@dataclass
class FileSteps:
    main_file: StepResult = field(default_factory=lambda: StepResult())
    last_world_file: StepResult = field(default_factory=lambda: StepResult())
    newest_year: StepResult = field(default_factory=lambda: StepResult())
    source: StepResult = field(default_factory=lambda: StepResult())
    slug: StepResult = field(default_factory=lambda: StepResult())


@dataclass
class TemplateInfo:
    """
    Holds all state for a single template being processed.
    """

    id: int
    title: str
    new_main_file: str
    last_world_file: str
    newest_year: int | None
    source: str
    status: str = "processing"
    error: str | None = None
    error_type: str | None = None
    steps: FileSteps = field(default_factory=lambda: FileSteps())

    def to_dict(self) -> dict[str, Any]:
        """
        convert to dict.
        """
        return asdict(self)


@dataclass
class CollectTemplatesDataWorkerObject(StandardAdminWorkerObject):
    pages_added: list[dict[str, Any]] = field(default_factory=list)
    pages_updated: list[dict[str, Any]] = field(default_factory=list)


_old_result = {
    "note": "",
    "status": "pending",
    "errors": [],
    "args": {},
    "job_id": "self.job_id",
    "started_at": "datetime.now().isoformat()",
    "completed_at": None,
    "cancelled_at": None,
    "summary": {
        "total": 0,
        "processed": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
    },
    "pages_processed": [],
    "pages_added": [],
    "pages_updated": [],
    "pages_skipped": [],
    "pages_failed": [],
}

__all__ = [
    "CollectTemplatesDataWorkerObject",
]
