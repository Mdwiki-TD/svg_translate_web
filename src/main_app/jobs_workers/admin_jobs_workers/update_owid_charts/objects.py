"""
Objects for update_owid_charts worker.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ....db.models import OwidChartRecord
from ...shared_objects import StandardAdminWorkerObject


@dataclass
class ChartUpdateInfo:
    chart_id: int
    slug: str
    status: str = "pending"  # updated | skipped | failed
    skip_reason: str | None = None
    status_404: int | None = None
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # old values (before update)
    old_min_time: int | None = None
    old_max_time: int | None = None
    old_len_years: int | None = None

    # new values (from API)
    new_min_time: int | None = None
    new_max_time: int | None = None
    new_len_years: int | None = None

    owid_variable_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "chart_id": self.chart_id,
            "slug": self.slug,
            "status": self.status,
            "skip_reason": self.skip_reason,
            "error": self.error,
            "timestamp": self.timestamp,
            "old_min_time": self.old_min_time,
            "old_max_time": self.old_max_time,
            "old_len_years": self.old_len_years,
            "new_min_time": self.new_min_time,
            "new_max_time": self.new_max_time,
            "new_len_years": self.new_len_years,
            "owid_variable_id": self.owid_variable_id,
        }

    @classmethod
    def from_chart(cls, chart: OwidChartRecord) -> ChartUpdateInfo:
        return cls(
            chart_id=chart.chart_id,
            slug=chart.slug,
            old_min_time=chart.min_time,
            old_max_time=chart.max_time,
            old_len_years=chart.len_years,
            owid_variable_id=chart.owid_variable_id,
        )


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

    metadata_keys: set[str] = field(default_factory=set)


__all__ = [
    "UpdateOwidChartsWorkerObject",
    "UpdateOwidChartsSummary",
]
