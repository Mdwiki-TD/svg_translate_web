"""
Objects for update_owid_charts worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from ....database.models import OwidChartRecord
from ...shared_objects import StandardAdminWorkerObject


@dataclass
class StepInfo:
    success: bool | None = None
    before: str | int | None = None
    after: str | int | None = None

    def _update(self, after: str | int | None) -> None:
        if after and self.before != after:
            self.after = after

@dataclass
class ChartNewInfo:
    chart_id: int
    slug: str
    status: str = "pending"  # updated | skipped | failed
    skip_reason: str | None = None
    status_404: int | None = None
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # —————————————————————————
    # New steps values
    min_time: StepInfo = field(default_factory=StepInfo)
    max_time: StepInfo = field(default_factory=StepInfo)
    len_years: StepInfo = field(default_factory=StepInfo)
    variable_id: StepInfo = field(default_factory=StepInfo)
    source: StepInfo = field(default_factory=StepInfo)

    # —————————————————————————

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_chart(cls, chart: OwidChartRecord) -> ChartNewInfo:
        data = cls(
            chart_id=chart.chart_id,
            slug=chart.slug,
            source=chart.source,
        )
        data.min_time.before = chart.min_time
        data.max_time.before = chart.max_time
        data.len_years.before = chart.len_years
        data.variable_id.before = chart.owid_variable_id
        return data


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


@dataclass
class ChartUpdateInfo:
    chart_id: int
    slug: str
    status: str = "pending"  # updated | skipped | failed
    skip_reason: str | None = None
    status_404: int | None = None
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # —————————————————————————
    # Legacy to be removed
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
        return asdict(self)

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


__all__ = [
    "UpdateOwidChartsWorkerObject",
    "UpdateOwidChartsSummary",
]
