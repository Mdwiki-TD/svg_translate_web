"""Objects for update_owid_charts worker."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

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


__all__ = [
    "UpdateOwidChartsWorkerObject",
    "UpdateOwidChartsSummary",
]
