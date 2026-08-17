"""Shared objects for job workers."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal

logger = logging.getLogger(__name__)


@dataclass
class SharedMapToJson:
    def to_json(self) -> dict[str, Any]:
        """
        Converts the dataclass instance back to its original dictionary format.
        """
        return asdict(self)  # pyright: ignore[reportCallIssue]


@dataclass(frozen=True)
class UpdaterOutcome:
    """Result of running the updater on one page."""

    kind: Literal["missing", "changed", "error", "skipped"]
    newrevid: int = 0
    msg: str = ""

    def to_json(self) -> dict[str, Any]:
        """
        Converts the dataclass instance back to its original dictionary format.
        """
        return asdict(self)  # pyright: ignore[reportCallIssue]


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
class WorkerObject(SharedMapToJson):
    note: str | None = None
    status: str = "pending"
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

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_start(cls, job_id: int, args: dict[str, Any]) -> Any:
        return cls(
            job_id=job_id,
            args=args,
        )


@dataclass
class SharedworkerObject(WorkerObject):
    summary: Summary = field(default_factory=Summary)

    pages_processed: list[dict[str, Any]] = field(default_factory=list)

    pages_changed: list[dict[str, Any]] = field(default_factory=list)
    pages_errors: list[dict[str, Any]] = field(default_factory=list)
    pages_skipped: list[dict[str, Any]] = field(default_factory=list)

    pages_missing: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class StandardAdminWorkerObject(WorkerObject):
    summary: StandardAdminSummary = field(default_factory=StandardAdminSummary)
    pages_processed: list[dict[str, Any]] = field(default_factory=list)
    pages_success: list[dict[str, Any]] = field(default_factory=list)
    pages_skipped: list[dict[str, Any]] = field(default_factory=list)
    pages_failed: list[dict[str, Any]] = field(default_factory=list)
    note: str = ""
    args: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "Summary",
    "SharedworkerObject",
    "UpdaterOutcome",
    "StandardAdminSummary",
    "StandardAdminWorkerObject",
]
