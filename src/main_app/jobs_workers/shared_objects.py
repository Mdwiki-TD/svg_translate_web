"""Shared objects for job workers."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal

logger = logging.getLogger(__name__)

STATUS_LITERAL = Literal["cancelled", "completed", "failed", "pending", "running", "skipped", "success"]

STATUS_LIST = Literal["completed", "created", "failed", "pending", "skipped", "updated", "uploaded"]

STATUS_LIST3 = Literal["failed", "pending", "redirected", "renamed", "skipped_target_exists"]


@dataclass
class OneStep:
    result: bool | None = None
    msg: str | None = None
    newrevid: int = 0


@dataclass
class SharedMapToJson:
    def to_json(self) -> dict[str, Any]:
        """
        Converts the dataclass instance back to its original dictionary format.
        """
        return asdict(self)


@dataclass(frozen=True)
class UpdaterOutcome:
    """Result of running the updater on one page."""

    status: Literal["missing", "changed", "error", "skipped"]
    newrevid: int = 0
    msg: str = ""

    def to_json(self) -> dict[str, Any]:
        """
        Converts the dataclass instance back to its original dictionary format.
        """
        return asdict(self)


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
    # changed: int = 0
    # errors: int = 0
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
class SharedworkerObject(WorkerMapping):
    summary: Summary = field(default_factory=Summary)

    pages_processed: list[dict[str, Any]] = field(default_factory=list)

    pages_changed: list[dict[str, Any]] = field(default_factory=list)
    pages_errors: list[dict[str, Any]] = field(default_factory=list)
    pages_skipped: list[dict[str, Any]] = field(default_factory=list)

    pages_missing: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class StandardAdminWorkerObject(WorkerMapping):
    summary: StandardAdminSummary = field(default_factory=StandardAdminSummary)
    pages_processed: list[dict[str, Any]] = field(default_factory=list)
    pages_success: list[dict[str, Any]] = field(default_factory=list)
    pages_skipped: list[dict[str, Any]] = field(default_factory=list)
    pages_failed: list[dict[str, Any]] = field(default_factory=list)
    note: str = ""
    args: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "OneStep",
    "Summary",
    "SharedworkerObject",
    "UpdaterOutcome",
    "StandardAdminSummary",
    "StandardAdminWorkerObject",
]
