"""Admin-only routes for managing coordinator access."""

from __future__ import annotations

import logging
from typing import Any

from flask import (
    Blueprint,
    render_template,
    request,
)

from ..db.services import list_jobs
from ..jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins
from ..public.utils.routes_utils import get_job_detail_url
from .decorators import admin_required
from .sidebar import create_side

logger = logging.getLogger(__name__)

bp_admin = Blueprint("admin", __name__, url_prefix="/admin")


def _get_display_name(job_type: str) -> str:
    job_data = jobs_data_admins.get(job_type)
    return job_data.job_name if job_data else job_type


@bp_admin.app_context_processor
def inject_sidebar() -> dict[str, Any]:
    path_parts = request.path.strip("/").split("/")
    active_route = path_parts[1] if len(path_parts) > 1 else ""
    # logger.debug(f"Injecting sidebar for path='{request.path}', {active_route=}")
    sidebar_html = create_side(active_route=active_route, path=request.path)
    return {"sidebar": sidebar_html}


@bp_admin.route("/", methods=["GET"])
@admin_required
def admin_dashboard() -> str:
    jobs = list_jobs(limit=100)

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
    "bp_admin",
]
