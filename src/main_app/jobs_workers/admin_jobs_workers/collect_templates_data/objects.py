"""
Objects for collect_templates_data worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class StepResult:
    """
    "main_file": {"result": None, "value": "", "new_value": "", "msg": ""},
    """

    result: bool | str | None = None
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
        return asdict(self)  # pyright: ignore[reportCallIssue]


@dataclass
class TemplateData:
    id: int = 0
    title: str = ""
    main_file: str | None = None
    last_world_file: str | None = None
    last_world_year: int | None = None
    slug: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        if self.main_file:
            self.main_file = self.main_file.removeprefix("File:")
        if self.last_world_file:
            self.last_world_file = self.last_world_file.removeprefix("File:")


@dataclass
class CollectTemplatesDataWorkerObject(StandardAdminWorkerObject):
    pages_added: list[dict[str, Any]] = field(default_factory=list)
    pages_updated: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "CollectTemplatesDataWorkerObject",
]
