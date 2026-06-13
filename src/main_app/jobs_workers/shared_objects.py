"""Shared objects for job workers."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal, Optional

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpdaterOutcome:
    """Result of running the updater on one page."""

    kind: Literal["missing", "changed", "error", "skipped"]
    newrevid: int = 0
    msg: str = ""

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StandardAdminSummary:
    total: int = 0
    processed: int = 0
    success: int = 0
    failed: int = 0
    skipped: int = 0


@dataclass
class Summary:
    total: int = 0
    processed: int = 0


@dataclass
class WorkerObject:
    """
    "note": "",
    "status": "pending",
    "job_id": self.job_id,

    "started_at": datetime.now().isoformat(),
    "completed_at": None,
    "cancelled_at": None,
    "last_update": None,
    "failed_at": None,

    "errors": [],
    "args": {},

    "pages_processed": [],
    "pages_uploaded": [],
    "pages_updated": [],
    "pages_skipped": [],
    "pages_failed": [],
    """

    note: Optional[str] = None
    status: str = "pending"
    job_id: int = 0

    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    last_update: Optional[str] = ""
    failed_at: Optional[str] = None

    errors: list[dict[str, Any]] = field(default_factory=list)
    args: dict[str, Any] = field(default_factory=dict)

    error: Optional[str] = None
    error_type: Optional[str] = None

    def to_json(self) -> dict[str, Any]:
        """
        Converts the dataclass instance back to its original dictionary format.
        """

        return asdict(self)


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
