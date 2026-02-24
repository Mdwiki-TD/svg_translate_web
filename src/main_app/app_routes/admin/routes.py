"""Admin-only routes for managing coordinator access."""

from __future__ import annotations
import logging

from flask import (
    Blueprint,
    redirect,
    request,
    url_for,
)

from ...admins.admins_required import admin_required
from .admin_routes.coordinators import Coordinators
from .admin_routes.jobs import Jobs
from .admin_routes.recent import Recent
from .admin_routes.templates import Templates
from .sidebar import create_side

logger = logging.getLogger(__name__)

bp_admin = Blueprint("admin", __name__, url_prefix="/admin")


@bp_admin.app_context_processor
def inject_sidebar():
    path_parts = request.path.strip("/").split("/")
    active_route = path_parts[1] if len(path_parts) > 1 else ""
    logger.debug(f"Injecting sidebar for path='{request.path}'")
    sidebar_html = create_side(active_route=active_route)
    return dict(sidebar=sidebar_html)


@bp_admin.get("/")
@admin_required
def admin_dashboard():
    return redirect(url_for("admin.recent_routes"))


Coordinators(bp_admin)

Recent(bp_admin)

Templates(bp_admin)

Jobs(bp_admin)
