"""
Worker module for update_owid_charts.

For every chart in the ``owid_charts`` table:
  1. Fetch ``https://ourworldindata.org/grapher/{slug}.metadata.json``
  2. Find the first column entry that has a ``timespan`` field
     (format ``"YYYY-YYYY"`` or ``"YYYY"``)
  3. Parse ``min_time``, ``max_time``, and ``len_years`` from the timespan
  4. If any of those three values differ from the DB record → update

Skipped reasons:
  - ``no_timespan``  – no column with a ``timespan`` key was found in the JSON
  - ``no_change``    – fetched values are identical to current DB values
  - ``fetch_error``  – HTTP / network / JSON-decode error
"""

from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from ...api_services.clients.owid_client import fetch_grapher_metadata
from ...db.models.owid_charts import OwidChartRecord
from ...db.services import owid_charts_service
from ..base_worker import BaseJobWorker

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Timespan helpers
# ---------------------------------------------------------------------------


def _parse_timespan(timespan: str) -> tuple[int, int, int] | None:
    """Parse a ``"YYYY-YYYY"`` or ``"YYYY"`` timespan string.

    Returns ``(min_time, max_time, len_years)`` or ``None`` if unparseable.
    """

    match = re.match(r"^(-?\d+)(?:-(-?\d+))?$", timespan.strip())
    if not match:
        return None
    try:
        min_t = int(match.group(1))
        max_t = int(match.group(2)) if match.group(2) is not None else min_t
    except ValueError:
        return None

    len_y = max_t - min_t + 1
    return min_t, max_t, len_y


def _first_value(columns: dict, key: str) -> str | Any:
    """Return the first ``key`` value found among the column entries."""
    for col_data in columns.values():
        if isinstance(col_data, dict) and key in col_data:
            return col_data[key]
    return None


# ---------------------------------------------------------------------------
# Per-chart result dataclass
# ---------------------------------------------------------------------------


@dataclass
class ChartUpdateInfo:
    chart_id: int
    slug: str
    status: str = "pending"  # updated | skipped | failed
    skip_reason: str | None = None
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


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------


class UpdateOwidChartsWorker(BaseJobWorker):
    """Refresh ``min_time`` / ``max_time`` / ``len_years`` for every OWID chart."""

    def __init__(
        self,
        job_id: int,
        user: dict[str, Any],
        cancel_event: threading.Event | None = None,
        args: dict[str, Any] | None = None,
    ) -> None:
        self.limit_items = args.get("limit_items") if args else 0

        super().__init__(job_id, user, cancel_event)
        self.result: Dict[str, Any] = self.get_initial_result()

    def get_job_type(self) -> str:
        return "update_owid_charts"

    def get_initial_result(self) -> Dict[str, Any]:
        return {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
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

    # ------------------------------------------------------------------
    # Per-chart processing
    # ------------------------------------------------------------------

    def _process_chart(self, chart: OwidChartRecord) -> bool:
        info = ChartUpdateInfo(
            chart_id=chart.chart_id,
            slug=chart.slug,
            old_min_time=chart.min_time,
            old_max_time=chart.max_time,
            old_len_years=chart.len_years,
            owid_variable_id=chart.owid_variable_id,
        )

        # 1 A). Fetch metadata
        metadata = fetch_grapher_metadata(chart.slug)
        if metadata is None:
            info.status = "failed"
            info.error = "Could not fetch metadata JSON"
            self.result["failed_charts"].append(
                {
                    "status": "failed",
                    "slug": chart.slug,
                    "error": "Could not fetch metadata JSON",
                }
            )
            return False

        data = {}

        # 1 B) Find slug redirect
        original_chart_url = metadata.get("chart", {}).get("originalChartUrl", "")
        if original_chart_url and "/grapher/" in original_chart_url:
            original_slug = original_chart_url.split("/grapher/", maxsplit=1)[1].split("?")[0]
            if original_slug != chart.slug:
                data["slug"] = original_slug
                # TODO: find any template use slug and replace it by new slug, or create database table for slug redirects

        # 2. Find a timespan
        columns = metadata.get("columns", {})
        timespan_raw = _first_value(columns, "timespan")
        owid_variable_id = _first_value(columns, "owidVariableId")

        if not timespan_raw and not owid_variable_id and not data:
            info.status = "skipped"
            info.skip_reason = "nothing to update"
            self.result["skipped_charts"].append(
                {
                    "status": "skipped",
                    "slug": chart.slug,
                    "skip_reason": "nothing to update",
                }
            )
            return False

        if owid_variable_id and owid_variable_id != chart.owid_variable_id:
            info.owid_variable_id = owid_variable_id
            data.update(
                {
                    "owid_variable_id": owid_variable_id,
                }
            )

        if timespan_raw:
            # 3. Parse timespan
            parsed = _parse_timespan(timespan_raw)
            # here we set status to failed if no parsed and no owid_variable_id to update.
            if parsed is None and not data:
                info.status = "failed"
                info.error = f"Could not parse timespan: '{timespan_raw}'"
                self.result["failed_charts"].append(
                    {
                        "status": "failed",
                        "slug": chart.slug,
                        "error": f"Could not parse timespan: '{timespan_raw}'",
                    }
                )
                return False

            if parsed:
                min_t, max_t, len_y = parsed

                info.new_min_time = min_t if min_t != info.old_min_time else None
                info.new_max_time = max_t if max_t != info.old_max_time else None
                info.new_len_years = len_y if len_y != info.old_len_years else None

                # 4. Compare — skip if nothing changed
                if min_t == chart.min_time and max_t == chart.max_time and len_y == chart.len_years:
                    logger.info(f"Chart '{chart.slug}' has no changes in timespan")
                else:
                    data.update(
                        {
                            "min_time": min_t,
                            "max_time": max_t,
                            "len_years": len_y,
                        }
                    )

        # 5. Update DB
        if not data:
            info.status = "skipped"
            info.skip_reason = "nothing to update"
            self.result["skipped_charts"].append(
                {
                    "status": "skipped",
                    "slug": chart.slug,
                    "skip_reason": "nothing to update",
                }
            )
            return False

        try:
            owid_charts_service.update_chart_data(
                chart.chart_id,
                data,
            )
            info.status = "updated"
            self.result["updated_charts"].append(info.to_dict())
            return True
        except Exception as exc:
            logger.exception(f"Job {self.job_id}: DB update failed for chart '{chart.slug}'")
            info.status = "failed"
            info.error = str(exc)

        self.result["failed_charts"].append(info.to_dict())
        return False

    def _load_charts(self) -> list[OwidChartRecord]:
        charts = owid_charts_service.list_charts()
        return self._apply_limits(charts)

    def _apply_limits(self, charts: list[OwidChartRecord]) -> list[OwidChartRecord]:
        _limit = self.limit_items if isinstance(self.limit_items, int) else 0
        if _limit > 0 and len(charts) > _limit:
            logger.info(f"Job {self.job_id}: limiting from {len(charts)} to {_limit} page")
            return charts[:_limit]

        return charts

    # ------------------------------------------------------------------
    # BaseJobWorker.process
    # ------------------------------------------------------------------

    def process(self) -> Dict[str, Any]:
        charts = self._load_charts()
        total = len(charts)
        self.result["summary"]["total"] = total
        logger.info(f"Job {self.job_id}: Found {total} charts to process")

        per_item = self.get_priority(total)

        for n, chart in enumerate(charts, start=1):
            if self.is_cancelled():
                break

            logger.info(f"Job {self.job_id}: Processing {n}/{total}: {chart.slug}")
            changed = self._process_chart(chart)
            self.result["summary"]["processed"] += 1

            if changed and self.check_cancel_db_periodic():
                logger.info(f"Job {self.job_id}: Cancelled due to periodic check")
                break

            if n == 1 or n % per_item == 0:
                self._save_progress()

        if self.result.get("status") in ("pending", "running"):
            self.result["status"] = "completed"

        return self.result


# ---------------------------------------------------------------------------
# Entry-point (called by the thread runner)
# ---------------------------------------------------------------------------


def update_owid_charts_worker_entry(
    *,
    job_id: int,
    user: dict[str, Any],
    cancel_event: threading.Event | None = None,
    args: dict[str, Any] | None = None,
) -> None:
    """Background worker entry-point for update_owid_charts."""
    logger.info(f"Starting job {job_id}: update OWID charts timespan data")

    if args and args.get("owid_charts_limit_items"):
        args.update({"limit_items": args.get("owid_charts_limit_items")})

    worker = UpdateOwidChartsWorker(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=args,
    )
    worker.run()


__all__ = [
    "UpdateOwidChartsWorker",
    "update_owid_charts_worker_entry",
]
