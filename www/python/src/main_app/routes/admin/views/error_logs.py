"""
Admin-only routes for browsing the error log tables.

- error_logs_view:      overall (all-time) stats, stats for the selected period and
                        the detailed rows (only the last DETAIL_RETENTION_DAYS exist)
- error_log_path_view:  per-day history of one failing path
"""

from __future__ import annotations

import logging

from flask import Blueprint, redirect, render_template, request, url_for
from flask.views import MethodView

from ....database.services.error_log_service import DETAIL_RETENTION_DAYS, ErrorLogService
from ....decorators import admin_required

logger = logging.getLogger(__name__)


PER_PAGE = 50
MAX_DAYS = 365
OVERALL_LIMIT = 100  # rows in the all-time "top failing paths" table
PERIOD_LIMIT = 25  # rows in the selected-period "top failing paths" table
HISTORY_DEFAULT_DAYS = 90


class ErrorLogsView(MethodView):
    """View to browse, filter and paginate error log rows stored in the database."""

    decorators = [admin_required]

    @staticmethod
    def _parse_filters() -> dict:
        """Read and sanitize filters from the query string."""
        days = request.args.get("days", 7, type=int)
        bot = request.args.get("bot", "")
        return {
            "days": min(max(days, 1), MAX_DAYS),
            "status_code": request.args.get("status", type=int),
            "path": request.args.get("path", "").strip()[:200],
            "ip": request.args.get("ip", "").strip()[:45],
            # "" = any, "1" = suspected bots only, "0" = real browsers only
            "suspected_bot": {"1": True, "0": False}.get(bot),
        }

    def get(self) -> str:
        """Render the error log page with overall stats, period stats, filters and rows."""
        filters = self._parse_filters()
        page = max(request.args.get("page", 1, type=int), 1)

        service = ErrorLogService()

        # Detailed rows exist only for DETAIL_RETENTION_DAYS; statistics come from
        # the long-term daily counters and can cover the whole requested period
        search_filters = {**filters, "days": min(filters["days"], DETAIL_RETENTION_DAYS)}
        pagination = service.search(**search_filters, page=page, per_page=PER_PAGE)

        summary = service.status_summary(filters["days"])
        top_paths = service.top_paths(days=filters["days"], limit=PERIOD_LIMIT)

        # Active filters only, reused by the form and the pagination links
        link_args = {
            "days": filters["days"],
            "status": filters["status_code"],
            "path": filters["path"] or None,
            "ip": filters["ip"] or None,
            "bot": request.args.get("bot") or None,
        }

        return render_template(
            "admins/error_logs.html",
            pagination=pagination,
            summary=summary,
            total_hits=sum(row["hits"] for row in summary),
            total_bot_hits=sum(row["bot_hits"] for row in summary),
            top_paths=top_paths,
            detail_days=DETAIL_RETENTION_DAYS,
            detail_limited=filters["days"] > DETAIL_RETENTION_DAYS,
            filters=link_args,
        )


class ErrorLogsStatisticsView(MethodView):
    decorators = [admin_required]

    def get(self) -> str:
        """Render the overall stats page."""

        service = ErrorLogService()

        # All-time statistics (days=None)
        overall_summary = service.status_summary(days=None)
        overall_paths = service.top_paths(days=None, limit=OVERALL_LIMIT)

        return render_template(
            "admins/error_logs_statistics.html",
            overall_summary=overall_summary,
            overall_total_hits=sum(row["hits"] for row in overall_summary),
            overall_total_bot_hits=sum(row["bot_hits"] for row in overall_summary),
            overall_paths=overall_paths,
            overall_limit=OVERALL_LIMIT,
        )


class ErrorPathHistoryView(MethodView):
    """Per-day hit counts for one failing path (read from the daily counters)."""

    decorators = [admin_required]

    def get(self):
        """Render the day-by-day history of the requested path."""
        path = request.args.get("path", "").strip()[:500]
        if not path:
            return redirect(url_for(".error_logs"))

        days = request.args.get("days", HISTORY_DEFAULT_DAYS, type=int)
        days = min(max(days, 1), MAX_DAYS)

        history = ErrorLogService().path_history(path, days=days)
        total_hits = sum(row["hits"] for row in history)
        total_bot_hits = sum(row["bot_hits"] for row in history)
        peak = max(history, key=lambda row: row["hits"], default=None)

        return render_template(
            "admins/error_log_path.html",
            path=path,
            days=days,
            history=history,
            total_hits=total_hits,
            total_bot_hits=total_bot_hits,
            max_hits=peak["hits"] if peak else 0,
            peak=peak,
        )


class CheckErrorLogsView:
    """Registrar class to bind the error logs MethodViews to a Blueprint."""

    @staticmethod
    def register(bp: Blueprint) -> None:
        """Register error logs URL rules on the provided blueprint."""
        bp.add_url_rule("/", view_func=ErrorLogsView.as_view("error_logs"))
        bp.add_url_rule("/statistics", view_func=ErrorLogsStatisticsView.as_view("error_logs_statistics"))
        bp.add_url_rule("/path", view_func=ErrorPathHistoryView.as_view("error_log_path"))


__all__ = [
    "CheckErrorLogsView",
    "ErrorLogsView",
    "ErrorPathHistoryView",
]
