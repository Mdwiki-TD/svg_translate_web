"""Shared objects for job workers."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal

logger = logging.getLogger(__name__)

STATUS_LITERAL = Literal[
    "cancelled",
    "completed",
    "created",
    "failed",
    "pending",
    "running",
    "skipped",
    "success",
    "updated",
    "uploaded",
]

OUTCOME_STATUS = Literal[
    "pending",
    "running",
    "changed",
    "completed",
    "missing",
    "skipped",
    "error",
    "failed",
    "updated",
]


@dataclass
class OneStep:
    result: bool | None = None
    msg: str | None = None
    newrevid: int = 0


@dataclass
class StepInfo:
    success: bool | None = None
    before: str | int | None = None
    after: str | int | None = None

    def _update_if_diff(self, after: str | int | None) -> None:
        if after and self.before != after:
            self.after = after


@dataclass
class SharedMapToJson:
    def to_json(self) -> dict[str, Any]:
        """
        Converts the dataclass instance back to its original dictionary format.
        """
        return asdict(self)


@dataclass
class UpdaterOutcome(SharedMapToJson):
    """Result of running the updater on one page."""

    status: OUTCOME_STATUS = "pending"
    title: str = ""
    msg: str = ""
    newrevid: int = 0
    error_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class StandardAdminSummary(SharedMapToJson):
    total: int = 0
    processed: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0


@dataclass
class Summary(SharedMapToJson):
    total: int = 0
    processed: int = 0


@dataclass
class WorkerMapping(SharedMapToJson):
    note: str | None = None
    status: STATUS_LITERAL = "pending"
    job_id: int = 0

    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: str | None = None
    cancelled_at: str | None = None
    last_update: str | None = ""
    failed_at: str | None = None
    final_status_updated: bool | None = None

    errors: list[dict[str, Any]] = field(default_factory=list)
    args: dict[str, Any] = field(default_factory=dict)

    error: str | None = None
    error_type: str | None = None


@dataclass
class OneItem(SharedMapToJson):
    title: str = ""
    status: STATUS_LITERAL = "pending"


@dataclass
class SharedworkerObject(WorkerMapping):
    summary: Summary = field(default_factory=Summary)

    pages_processed: list[OneItem] = field(default_factory=list)
    pages_missing: list[OneItem] = field(default_factory=list)
    pages_skipped: list[OneItem] = field(default_factory=list)
    pages_updated: list[OneItem] = field(default_factory=list)
    pages_failed: list[OneItem] = field(default_factory=list)


@dataclass
class StandardAdminWorkerObject(WorkerMapping):
    summary: StandardAdminSummary = field(default_factory=StandardAdminSummary)
    pages_processed: list[OneItem] = field(default_factory=list)
    pages_success: list[OneItem] = field(default_factory=list)
    pages_skipped: list[OneItem] = field(default_factory=list)
    pages_failed: list[OneItem] = field(default_factory=list)
    args: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "OneStep",
    "Summary",
    "UpdaterOutcome",
    "SharedworkerObject",
    "StandardAdminSummary",
    "StandardAdminWorkerObject",
]
