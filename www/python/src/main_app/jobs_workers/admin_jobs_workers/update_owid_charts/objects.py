"""
Objects for update_owid_charts worker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from ....database.models import OwidChartRecord
from ...shared_objects import STATUS_LIST, STATUS_LITERAL, StandardAdminWorkerObject


@dataclass
class StepInfo:
    success: bool | None = None
    before: str | int | None = None
    after: str | int | None = None

    def _update_if_diff(self, after: str | int | None) -> None:
        if after and self.before != after:
            self.after = after


@dataclass
class ChartNewInfo:
    chart_id: int
    slug: str
    status: STATUS_LIST = "pending"  # updated | skipped | failed
    skip_reason: str | None = None
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # —————————————————————————
    # New steps values
    source: StepInfo = field(default_factory=StepInfo)

    min_time: StepInfo = field(default_factory=StepInfo)
    max_time: StepInfo = field(default_factory=StepInfo)
    len_years: StepInfo = field(default_factory=StepInfo)
    variable_id: StepInfo = field(default_factory=StepInfo)

    # —————————————————————————

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_chart(cls, chart: OwidChartRecord) -> ChartNewInfo:
        return cls(
            chart_id=chart.chart_id,
            slug=chart.slug,
            source=StepInfo(before=chart.source),
            min_time=StepInfo(before=chart.min_time),
            max_time=StepInfo(before=chart.max_time),
            len_years=StepInfo(before=chart.len_years),
            variable_id=StepInfo(before=chart.owid_variable_id),
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


@dataclass
class ChartUpdateInfo:
    chart_id: int
    slug: str
    status: STATUS_LITERAL = "pending"  # updated | skipped | failed
    skip_reason: str | None = None
    error: str | None = None

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


__all__ = [
    "UpdateOwidChartsWorkerObject",
    "UpdateOwidChartsSummary",
]
