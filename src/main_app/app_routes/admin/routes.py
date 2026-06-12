"""Admin-only routes for managing coordinator access."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    request,
)

from ...db.services import list_jobs
from ...jobs_workers.admin_jobs_workers.workers_list import jobs_data
from ..admin_routes import (
    coordinators_module,
    jobs_module,
    owidcharts_module,
    settings_module,
    slug_redirects_module,
    templates_module,
    users_module,
)
from ..utils.routes_utils import get_job_detail_url
from .admins_required import admin_required
from .sidebar import create_side

logger = logging.getLogger(__name__)

bp_admin = Blueprint("admin", __name__, url_prefix="/admin")


def _get_display_name(job_type: str) -> str:
    job_data = jobs_data.get(job_type)
    return job_data.job_name if job_data else job_type


@bp_admin.app_context_processor
def inject_sidebar():
    path_parts = request.path.strip("/").split("/")
    active_route = path_parts[1] if len(path_parts) > 1 else ""
    # logger.debug(f"Injecting sidebar for path='{request.path}', {active_route=}")
    sidebar_html = create_side(active_route=active_route, path=request.path)
    return {"sidebar": sidebar_html}


@bp_admin.get("/")
@admin_required
def admin_dashboard():
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


def register_blueprints(bp_admin) -> None:
    bp_admin.register_blueprint(coordinators_module.bp)
    bp_admin.register_blueprint(users_module.bp)
    bp_admin.register_blueprint(templates_module.bp)
    bp_admin.register_blueprint(settings_module.bp)
    bp_admin.register_blueprint(jobs_module.bp)
    bp_admin.register_blueprint(owidcharts_module.bp)
    bp_admin.register_blueprint(slug_redirects_module.bp)


register_blueprints(bp_admin)


__all__ = [
    "bp_admin",
]
