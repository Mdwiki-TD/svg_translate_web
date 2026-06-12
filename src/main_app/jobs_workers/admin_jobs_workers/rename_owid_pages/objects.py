"""
Objects for rename_owid_pages worker.

            "note": "",
            "status": "pending",
            "errors": [],
            "args": {},
            "job_id": self.job_id,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "cancelled_at": None,
            "summary": {
                "total": 0,
                "processed": 0,
                "checked": 0,
                "renamed": 0,
                "skipped_target_exists": 0,
                "redirected": 0,
                "failed": 0,
            },
            "pages_processed": [],
            "pages_success": [],
            "pages_skipped": [],
            "pages_failed": [],
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...shared_objects import StandardAdminWorkerObject


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


__all__ = [
    "RenameOwidPagesWorkerObject",
    "RenameOwidPagesSummary",
]
