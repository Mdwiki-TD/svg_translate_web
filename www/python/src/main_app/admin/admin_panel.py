"""Admin-only routes for the admin dashboard, built on MethodView."""

from __future__ import annotations

import logging
from typing import Any

from flask import (
    Blueprint,
    render_template,
    url_for,
)
from flask.views import MethodView

from ..database.services import JobsService
from ..decorators import admin_required
from ..jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins

logger = logging.getLogger(__name__)


def _get_display_name(job_type: str) -> str:
    """Return the human-friendly name registered for a job type."""
    job_data = jobs_data_admins.get(job_type)
    return job_data.job_name if job_data else job_type


class AdminDashboardView(MethodView):
    """View rendering the main admin dashboard."""

    decorators = [admin_required]

    def get(self) -> str:
        """List the most recent jobs with display names and detail URLs."""
        jobs = JobsService().list_jobs(limit=100)

        # Enhance jobs with display names and detail URLs
        enhanced_jobs: list[Any] = []
        for job in jobs:
            endpoint = (
                "admin_panel.jobs.job_detail" if job.job_type in jobs_data_admins else "public_jobs.job_detail"
            )
            detail_url = url_for(endpoint, job_type=job.job_type, job_id=job.id)

            enhanced_jobs.append(
                {
                    "id": job.id,
                    "status": job.status,
                    "job_type": job.job_type,
                    "display_name": _get_display_name(job.job_type),
                    "detail_url": detail_url,
                    "username": job.username,
                    "created_at": job.created_at,
                    "started_at": job.started_at,
                    "completed_at": job.completed_at,
                }
            )

        return render_template(
            "admins/admin.html",
            jobs=enhanced_jobs,
        )


class AdminPanel:
    """Admin Panel routes registrar using class-based views."""

    @classmethod
    def register(cls, bp: Blueprint) -> None:
        """Register the dashboard view and the sidebar context processor."""
        bp.add_url_rule(
            "/",
            view_func=AdminDashboardView.as_view("dashboard"),
            methods=["GET"],
        )


__all__ = [
    "AdminPanel",
]
