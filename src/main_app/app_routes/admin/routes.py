"""Admin-only routes for managing coordinator access."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    render_template,
    request,
)

from ...db.services import list_jobs
from ..admin_routes import (
    bp_coordinators,
    bp_jobs,
    bp_owidcharts,
    bp_settings,
    bp_templates,
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
    jobs = list_jobs(limit=100)
    job_type_names = {
        "collect_main_files": "Collect Templates data",
        "update_owid_charts": "Update OWID Charts",
        "crop_main_files": "Crop Newest World Files",
        "fix_nested_main_files": "Fix Nested Main Files",
        "create_owid_pages": "Create OWID Pages",
        "rename_owid_pages": "Rename OWID Pages",
        "add_svglanguages_template": "Add {{SVGLanguages}}",
        "download_main_files": "Download Main Files",
        "copy_svg_langs": "Copy SVG Translation",
        "fix_nested_jobs": "Fix Nested Tasks",
    }
    return render_template("admins/admin.html", jobs=jobs, job_type_names=job_type_names)


def register_blueprints(bp_admin) -> None:
    bp_admin.register_blueprint(bp_coordinators)
    bp_admin.register_blueprint(bp_templates)
    bp_admin.register_blueprint(bp_settings)
    bp_admin.register_blueprint(bp_jobs)
    bp_admin.register_blueprint(bp_owidcharts)


register_blueprints(bp_admin)
