"""
Objects for update_owid_charts worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ...shared_objects import StandardAdminWorkerObject


@dataclass
class UpdateOwidChartsSummary:
    total: int = 0
    processed: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0


@dataclass
class UpdateOwidChartsWorkerObject(StandardAdminWorkerObject):
    summary: UpdateOwidChartsSummary = field(default_factory=UpdateOwidChartsSummary)
    updated_charts: list[dict] = field(default_factory=list)
    skipped_charts: list[dict] = field(default_factory=list)
    failed_charts: list[dict] = field(default_factory=list)


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
        "updated": 0,
        "skipped": 0,
        "failed": 0,
    },
    "charts_processed": [],
    "updated_charts": [],
    "skipped_charts": [],
    "failed_charts": [],
}

__all__ = [
    "UpdateOwidChartsWorkerObject",
    "UpdateOwidChartsSummary",
]
