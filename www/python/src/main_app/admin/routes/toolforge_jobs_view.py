"""
Admin-only routes for browsing and managing the Toolforge jobs of this tool.

Thin HTTP layer: all the work is delegated to JobsPageService.
Endpoint names are relative to the blueprint (``url_for(".jobs")``).
"""

from __future__ import annotations

import logging

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask.views import MethodView
from werkzeug.wrappers import Response

from ...decorators import admin_required
from ..routes_services.toolforge_jobs_service import DEFAULT_LOG_LINES, JobsPageService

logger = logging.getLogger(__name__)


class BaseJobsView(MethodView):
    """Base view holding the shared service and HTTP helpers."""

    decorators = [admin_required]

    def __init__(self, service: JobsPageService | None = None) -> None:
        self.service = service or JobsPageService()

    @staticmethod
    def _flash_all(messages: list[tuple[str, str]]) -> None:
        """Flash every message returned by the service."""
        for text, category in messages:
            flash(text, category)


class JobsView(BaseJobsView):
    """View to list the Toolforge jobs and their current status."""

    def get(self) -> str:
        """Render the jobs table with a status summary."""
        page = self.service.build_jobs_page()
        self._flash_all(page.messages)
        return render_template(
            "admins/tf_jobs/index.html",
            **page.to_context(),
        )


class JobDetailView(BaseJobsView):
    """View to show a single job."""

    def get(self, job_id: str) -> str:
        """Render the details of one job."""
        page = self.service.build_job_page(job_id)
        self._flash_all(page.messages)
        return render_template(
            "admins/tf_jobs/job_details.html",
            **page.to_context(),
        )


class JobLogsView(BaseJobsView):
    """View to show the logs of a single job."""

    def get(self, job_id: str) -> str:
        """Render the last lines of the job logs."""
        lines = request.args.get("lines", DEFAULT_LOG_LINES, type=int)
        page = self.service.build_logs_page(job_id, lines)
        self._flash_all(page.messages)
        return render_template(
            "admins/tf_jobs/job_logs.html",
            **page.to_context(),
        )


class JobRestartView(BaseJobsView):
    """View to restart a job (POST only)."""

    def post(self, job_id: str) -> Response:
        """Restart the job, then go back to the jobs table."""
        result = self.service.restart_job(job_id)
        self._flash_all(result.messages)
        return redirect(url_for(f".{result.redirect_endpoint}"))


class JobDeleteView(BaseJobsView):
    """View to delete a job (POST only)."""

    def post(self, job_id: str) -> Response:
        """Delete the job, then go back to the jobs table."""
        result = self.service.delete_job(job_id)
        self._flash_all(result.messages)
        return redirect(url_for(f".{result.redirect_endpoint}"))


class ToolforgeJobsView:
    """Registrar class to bind the jobs MethodViews to a Blueprint."""

    @staticmethod
    def register(bp: Blueprint) -> None:
        """Register jobs URL rules on the provided blueprint."""
        bp.add_url_rule("/", view_func=JobsView.as_view("jobs"))
        bp.add_url_rule("/<job_id>", view_func=JobDetailView.as_view("job_detail"))
        bp.add_url_rule("/<job_id>/logs", view_func=JobLogsView.as_view("job_logs"))
        bp.add_url_rule("/<job_id>/restart", view_func=JobRestartView.as_view("job_restart"))
        bp.add_url_rule("/<job_id>/delete", view_func=JobDeleteView.as_view("job_delete"))


__all__ = [
    "ToolforgeJobsView",
    "JobDeleteView",
    "JobDetailView",
    "JobLogsView",
    "JobRestartView",
    "JobsView",
]
