"""Admin-only routes for managing coordinator access."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    redirect,
    request,
    url_for,
)

from ..admin_routes import (
    bp_jobs,
    bp_owidcharts,
    bp_settings,
    bp_templates,
    bp_coordinators,
)
from .admins_required import admin_required
from .sidebar import create_side

logger = logging.getLogger(__name__)

bp_admin = Blueprint("admin", __name__, url_prefix="/admin")


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
    return redirect(url_for("admin.templates.dashboard"))


def register_blueprints(bp_admin) -> None:
    bp_admin.register_blueprint(bp_coordinators)
    bp_admin.register_blueprint(bp_templates)
    bp_admin.register_blueprint(bp_settings)
    bp_admin.register_blueprint(bp_jobs)
    bp_admin.register_blueprint(bp_owidcharts)


register_blueprints(bp_admin)
