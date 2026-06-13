"""
Objects for create_owid_pages worker.

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
                "created": 0,
                "updated": 0,
                "failed": 0,
                "skipped": 0,
            },
            "pages_processed": [],
            "pages_created": [],
            "pages_updated": [],
            "pages_skipped": [],
            "pages_failed": [],
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class CreateOwidPagesSummary:
    total: int = 0
    processed: int = 0
    created: int = 0
    updated: int = 0
    failed: int = 0
    skipped: int = 0


@dataclass
class CreateOwidPagesWorkerObject(StandardAdminWorkerObject):
    summary: CreateOwidPagesSummary = field(default_factory=CreateOwidPagesSummary)
    pages_created: list[dict[str, Any]] = field(default_factory=list)
    pages_updated: list[dict[str, Any]] = field(default_factory=list)


__all__ = [
    "CreateOwidPagesWorkerObject",
    "CreateOwidPagesSummary",
]
