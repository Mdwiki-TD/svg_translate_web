"""
Admin-only routes for browsing the error_logs table.
"""

from __future__ import annotations

import logging

from flask import Blueprint, render_template, request
from flask.views import MethodView

from ...database.services.error_log_service import ErrorLogService
from ..decorators import admin_required

logger = logging.getLogger(__name__)

PER_PAGE = 50
MAX_DAYS = 365


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
        """Render the error log table with summary and filters."""
        filters = self._parse_filters()
        page = max(request.args.get("page", 1, type=int), 1)

        service = ErrorLogService()
        pagination = service.search(**filters, page=page, per_page=PER_PAGE)
        summary = service.status_summary(filters["days"])
        top_paths = service.top_paths(days=filters["days"], limit=10)

        # Active filters only, reused by the form and the pagination links
        link_args = {
            "days": filters["days"],
            "status": filters["status_code"],
            "path": filters["path"] or None,
            "ip": filters["ip"] or None,
            "bot": request.args.get("bot") or None,
        }

        return render_template(
            "admin/error_logs.html",
            pagination=pagination,
            summary=summary,
            total_hits=sum(row["hits"] for row in summary),
            total_bot_hits=sum(row["bot_hits"] for row in summary),
            top_paths=top_paths,
            filters=link_args,
        )


class CheckErrorLogsView:
    """Registrar class to bind the error logs MethodView to a Blueprint."""

    @staticmethod
    def register(bp: Blueprint) -> None:
        """Register error logs URL rules on the provided blueprint."""
        view = ErrorLogsView.as_view("error_logs")
        bp.add_url_rule("/", view_func=view)


__all__ = [
    "CheckErrorLogsView",
]
