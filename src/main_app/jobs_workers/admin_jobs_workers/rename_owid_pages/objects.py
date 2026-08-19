"""
Objects for rename_owid_pages worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from ...shared_objects import StandardAdminWorkerObject

STATUS_LIST = Literal["pending", "renamed", "skipped_target_exists", "failed", "redirected"]


@dataclass
class RenameInfo:
    """Holds the outcome of attempting to rename a single page."""

    namespace: int
    old_title: str
    new_title: str | None = None
    newrevid: int | None = None
    status: STATUS_LIST = "pending"
    msg: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "old_title": self.old_title,
            "new_title": self.new_title,
            "status": self.status,
            "msg": self.msg,
            "timestamp": self.timestamp,
        }


@dataclass
class RenameOwidPagesSummary:
    total: int = 0
    processed: int = 0
    checked: int = 0
    renamed: int = 0
    skipped_target_exists: int = 0
    redirected: int = 0
    failed: int = 0


@dataclass
class RenameOwidPagesWorkerObject(StandardAdminWorkerObject):
    summary: RenameOwidPagesSummary = field(default_factory=RenameOwidPagesSummary)
    pages_processed: list[dict[str, Any]] = field(default_factory=list)

    pages_renamed: list[dict[str, Any]] = field(default_factory=list)
    pages_redirected: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "RenameOwidPagesWorkerObject",
    "RenameOwidPagesSummary",
]
