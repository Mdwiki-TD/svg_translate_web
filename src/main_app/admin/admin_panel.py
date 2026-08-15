"""Admin-only routes for managing coordinator access."""

from __future__ import annotations

import logging
from typing import Any

from flask import (
    Blueprint,
    render_template,
)

from ..database.services import JobsService
from ..jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins
from ..public.utils.routes_utils import get_job_detail_url
from ..templates_markups import create_side
from .decorators import admin_required

logger = logging.getLogger(__name__)


def _get_display_name(job_type: str) -> str:
    job_data = jobs_data_admins.get(job_type)
    return job_data.job_name if job_data else job_type


class AdminPanel:
    """admin panel routes."""

    def __init__(self, bp: Blueprint) -> None:
        self.bp = bp
        self._setup_routes()

    def _setup_routes(self) -> None:
        self.bp.route("/", methods=["GET"])(admin_required(self.admin_dashboard))

        @self.bp.app_context_processor
        def inject_sidebar() -> dict[str, Any]:
            return {"create_side": create_side}

    def admin_dashboard(self) -> str:
        jobs = JobsService().list_jobs(limit=100)

        # Enhance jobs with display names and detail URLs
        enhanced_jobs: list[Any] = []
        for job in jobs:
            enhanced_jobs.append(
                {
                    "id": job.id,
                    "status": job.status,
                    "job_type": job.job_type,
                    "display_name": _get_display_name(job.job_type),
                    "detail_url": get_job_detail_url(job.id, job.job_type),
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


__all__ = [
    "AdminPanel",
]
