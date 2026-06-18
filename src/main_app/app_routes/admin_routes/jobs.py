"""Admin routes for managing background jobs."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    request,
    url_for,
)
from flask.typing import ResponseReturnValue
from werkzeug.wrappers.response import Response

from ...jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins
from ...jobs_workers.objects import JobData
from ...su_services import load_job_result
from ..admin.admins_required import admin_required
from ..jobs_routes_utils import (
    cancel_job_handler,
    delete_job_handler,
    job_detail_handler,
    jobs_list_handler,
    start_job_handler,
)

logger = logging.getLogger(__name__)

JOBS_BP = "admin.jobs"


class Jobs:
    """Jobs management routes."""

    def __init__(self, name: str, jobs_data_infos: dict[str, JobData], url_prefix: str) -> None:
        self.bp = Blueprint(name, __name__, url_prefix=url_prefix)
        self.jobs_data_infos: dict[str, JobData] = jobs_data_infos
        self._setup_routes()

    def _setup_routes(self) -> None:
        # ================================
        # Cancel Jobs routes
        # ================================

        @self.bp.post("/<string:job_type>/<int:job_id>/cancel")
        @admin_required
        def cancel_job(job_type: str, job_id: int) -> Response:
            if job_type not in self.jobs_data_infos:
                flash("Job type not found.", "warning")
                abort(404)

            result = cancel_job_handler(job_id, job_type)

            if result == "job_detail":
                return redirect(url_for(f"{JOBS_BP}.job_detail", job_type=job_type, job_id=job_id))

            return redirect(url_for(f"{JOBS_BP}.jobs_list", job_type=job_type))

        # ================================
        # Jobs List routes
        # ================================

        @self.bp.get("/<string:job_type>")
        @admin_required
        def jobs_list(job_type: str) -> str:
            template_data: JobData | None = self.jobs_data_infos.get(job_type)
            if not template_data:
                abort(404)

            return jobs_list_handler(job_type, template_data, bp_name=JOBS_BP)

        # ================================
        # Job Detail routes
        # ================================

        @self.bp.get("/<string:job_type>/<int:job_id>")
        @admin_required
        def job_detail(job_type: str, job_id: int) -> Response | str:
            # Load template data
            template_data: JobData | None = self.jobs_data_infos.get(job_type)

            if not template_data:
                abort(404)

            return job_detail_handler(job_id, job_type, template_data, bp_name=JOBS_BP)

        @self.bp.get("/<string:job_type>/<int:job_id>/expand")
        @admin_required
        def job_detail_expand(job_type: str, job_id: int) -> Response | str:
            # Load template data
            template_data: JobData | None = self.jobs_data_infos.get(job_type)

            if not template_data:
                abort(404)

            return job_detail_handler(job_id, job_type, template_data, bp_name=JOBS_BP, expand_all=True)

        # ================================
        # Start Job routes
        # ================================

        @self.bp.post("/<string:job_type>/start")
        @admin_required
        def start_job(job_type: str) -> ResponseReturnValue:
            if job_type not in self.jobs_data_infos:
                abort(404)

            args = request.form.to_dict()

            job_id = start_job_handler(job_type, args, bp_name=JOBS_BP)
            if not job_id:
                return redirect(url_for(f"{JOBS_BP}.jobs_list", job_type=job_type))

            return redirect(url_for(f"{JOBS_BP}.job_detail", job_type=job_type, job_id=job_id))

        # ================================
        # Delete Job routes
        # ================================

        @self.bp.post("/<string:job_type>/<int:job_id>/delete")
        @admin_required
        def delete_job(job_type: str, job_id: int) -> Response:
            if job_type not in self.jobs_data_infos:
                abort(404)
            result = delete_job_handler(job_id, job_type)

            if result == "job_detail":
                return redirect(url_for(f"{JOBS_BP}.job_detail", job_type=job_type, job_id=job_id))

            return redirect(url_for(f"{JOBS_BP}.jobs_list", job_type=job_type))

        @self.bp.get("/job-file/<string:result_file>/<string:job_type>")
        @admin_required
        def read_job_result_file(result_file: str, job_type: str) -> ResponseReturnValue:
            """ """
            if job_type not in self.jobs_data_infos:
                abort(404)
            result_data = load_job_result(result_file)
            return jsonify(result_data)


# Public API module
jobs_module = Jobs(
    name="jobs",
    jobs_data_infos=jobs_data_admins,
    url_prefix="/jobs",
)

__all__ = [
    "jobs_module",
]
