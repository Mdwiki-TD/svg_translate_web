"""
Worker module for update_owid_charts.

For every chart in the ``owid_charts`` table:
  1. Fetch ``https://ourworldindata.org/grapher/{slug}.metadata.json``
  2. Find the first column entry that has a ``timespan`` field
     (format ``"YYYY-YYYY"`` or ``"YYYY"``)
  3. Parse ``min_time``, ``max_time``, and ``len_years`` from the timespan
  4. Save the first column ``citationShort`` as the chart source citation
  5. Update any values that differ from the DB record

Skipped reasons:
  - ``no_timespan``  – no column with a ``timespan`` key was found in the JSON
  - ``no_change``    – fetched values are identical to current DB values
  - ``fetch_error``  – HTTP / network / JSON-decode error
"""

from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy.exc import OperationalError

from ....api_services import fetch_grapher_metadata_raw
from ....database.models import OwidChartRecord
from ....database.services import OwidChartsService
from ...base_worker import BaseObjectsJobWorker
from ...objects import JobsRunner
from ..slugs_helpers import check_slugs_url
from .objects import ChartNewInfo, UpdateOwidChartsWorkerObject

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Timespan helpers
# ---------------------------------------------------------------------------


def ensure_int(value: Any) -> int | None:
    """Ensure that a value is an integer or ``None``."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        pass
    return None


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
    except (TypeError, ValueError):
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
# Worker
# ---------------------------------------------------------------------------


class UpdateOwidChartsWorker(BaseObjectsJobWorker):
    """Refresh ``min_time`` / ``max_time`` / ``len_years`` for every OWID chart."""

    def __init__(self, data: JobsRunner) -> None:
        super().__init__(data)
        self.args = data.args or {}

        self.result: UpdateOwidChartsWorkerObject = UpdateOwidChartsWorkerObject(
            job_id=self.job_id,
            args=self.args,
        )

        self.limit_items = self.args.get("limit_items") or 0
        self.owid_charts_service = OwidChartsService()

    def get_job_type(self) -> str:
        """Return the job type identifier."""
        return "update_owid_charts"

    # ------------------------------------------------------------------
    # Per-chart processing
    # ------------------------------------------------------------------
    def _update_db(
        self,
        chart: OwidChartRecord,
        data: dict[str, Any],
        info: ChartNewInfo,
    ) -> bool:
        try:
            self.owid_charts_service.update_chart_data_with_retry(
                chart.chart_id,
                data,
            )

            return True
        except OperationalError as exc:
            info.status = "failed"
            info.error = str(exc)

            if exc.code == 2006:
                logger.error("Job %s: MySQL server has gone away", self.job_id)
            else:
                logger.exception("Job %s: DB update failed for chart '%s'", self.job_id, chart.slug)

        except Exception as exc:
            logger.exception("Job %s: DB update failed for chart '%s'", self.job_id, chart.slug)
            info.status = "failed"
            info.error = str(exc)
        return False

    def _process_one_item(self, chart: OwidChartRecord, info: ChartNewInfo) -> bool:

        # 1 A). Fetch metadata
        grapher_data = fetch_grapher_metadata_raw(chart.slug)

        if grapher_data.status_code == 404:
            self._update_db(chart, {"status_404": 404}, info)
            info.status = "failed"
            info.error = "Chart not found"
            return False

        if grapher_data.data is None:
            info.status = "failed"
            info.error = "Could not fetch metadata JSON"
            return False

        db_data: dict[str, Any] = {}

        # 1 B) Find slug redirect

        original_chart_url = grapher_data.data.get("chart", {}).get("originalChartUrl", "")

        check_slugs_url(chart.slug, original_chart_url)

        self.result.metadata_keys.update(list(grapher_data.data.keys()))

        # 2. Read values from the first applicable metadata column.
        columns = grapher_data.data.get("columns", {})
        timespan_raw = _first_value(columns, "timespan")
        owid_variable_id = _first_value(columns, "owidVariableId")
        citation_short = _first_value(columns, "citationShort")
        source = citation_short.strip() if isinstance(citation_short, str) else None

        if source and source != chart.source:
            info.source.after = source
            db_data["source"] = source

        if not timespan_raw and not owid_variable_id and not db_data:
            info.status = "skipped"
            info.skip_reason = "nothing to update"
            return False

        if owid_variable_id:
            owid_variable_id = ensure_int(owid_variable_id)
            if owid_variable_id != chart.owid_variable_id:
                info.variable_id.after = owid_variable_id
                db_data.update({"owid_variable_id": owid_variable_id})

        if timespan_raw:
            # 3. Parse timespan
            parsed = _parse_timespan(timespan_raw)
            # here we set status to failed if no parsed and no owid_variable_id to update.
            if parsed is None and not db_data:
                info.status = "failed"
                info.error = f"Could not parse timespan: '{timespan_raw}'"
                return False

            if parsed:
                min_t, max_t, len_y = parsed

                info.min_time._update_if_diff(after=min_t)
                info.max_time._update_if_diff(after=max_t)
                info.len_years._update_if_diff(after=len_y)
                # info.min_time.after = min_t if min_t != info.min_time.before else None
                # info.max_time.after = max_t if max_t != info.max_time else None
                # info.len_years.after = len_y if len_y != info.len_years else None

                # 4. Compare — skip if nothing changed
                if min_t == chart.min_time and max_t == chart.max_time and len_y == chart.len_years:
                    logger.info("Chart '%s' has no changes in timespan", chart.slug)
                else:
                    db_data.update({"min_time": min_t, "max_time": max_t, "len_years": len_y})

        # 5. Update DB
        if not db_data:
            info.status = "skipped"
            info.skip_reason = "nothing to update"
            return False

        updated = self._update_db(chart, db_data, info)
        if updated:
            info.status = "updated"
            return True

        info.status = "failed"
        return False

    def _load_charts(self) -> list[OwidChartRecord]:
        charts = self.owid_charts_service.list_charts()
        return self._apply_limits(charts)

    def _apply_limits(self, charts: list[OwidChartRecord]) -> list[OwidChartRecord]:
        _limit = self.limit_items if isinstance(self.limit_items, int) else 0
        if _limit > 0 and len(charts) > _limit:
            logger.info("Job %s: limiting from %d to %d page", self.job_id, len(charts), _limit)
            return charts[:_limit]

        return charts

    # ------------------------------------------------------------------
    # sub public entry-point
    # ------------------------------------------------------------------

    def process_one(self, chart_id: int) -> UpdateOwidChartsWorkerObject:
        chart = self.owid_charts_service.get_chart_by_id(chart_id)

        if not chart:
            logger.error(f"Job {self.job_id}: Chart '{chart_id}' not found")
            self.result.summary.total = 0
            self.result.status = "failed"
            self.log_errors(f"Chart '{chart_id}' not found")
            self.result.failed_charts.append(
                {
                    "status": "failed",
                    "slug": chart_id,
                    "error": "Chart not found",
                }
            )
            return self.result

        self.result.summary.total = 1
        logger.info("Job %d: Processing %s", self.job_id, chart.slug)

        info = ChartNewInfo.from_chart(chart)

        _changed = self._process_one_item(chart, info)
        self.update_status(chart.slug, info)

        self._save_progress()

        return self.result

    def process_all(self) -> UpdateOwidChartsWorkerObject:
        charts = self._load_charts()
        total = len(charts)

        self.result.summary.total = total
        logger.info("Job %s: Found %d charts to process", self.job_id, total)

        per_item = self.get_priority(total)

        for n, chart in enumerate(charts, start=1):
            if self.is_cancelled():
                break

            logger.info("Job %s: Processing %d/%d: %s", self.job_id, n, total, chart.slug)
            info = ChartNewInfo.from_chart(chart)

            changed = self._process_one_item(chart, info)
            self.update_status(chart.slug, info)

            if changed and self.check_cancel_db_periodic():
                logger.info("Job %s: Cancelled due to periodic check", self.job_id)
                break

            if n == 1 or n % per_item == 0:
                self._save_progress()

        return self.result

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    def process(self) -> UpdateOwidChartsWorkerObject:
        """Execute the collection processing logic."""
        if not self._check_site():
            return self.result

        # Single chart mode: if a chart_id arg is provided, process only that one
        if self.args.get("chart_id"):
            return self.process_one(self.args["chart_id"])

        # Default mode: process all charts
        return self.process_all()

    def update_status(self, slug: str, info: ChartNewInfo) -> None:
        self.result.summary.processed += 1

        if info.status == "failed":
            if info.error:
                self.result.failed_charts.append(
                    {
                        "status": "failed",
                        "slug": slug,
                        "error": info.error,
                    }
                )
            else:
                self.result.failed_charts.append(info.to_json())
        elif info.status == "skipped":
            self.result.skipped_charts.append(
                {
                    "status": "skipped",
                    "slug": slug,
                    "skip_reason": info.skip_reason,
                }
            )
        elif info.status == "updated":
            self.result.updated_charts.append(info.to_json())


__all__ = [
    "UpdateOwidChartsWorker",
]
