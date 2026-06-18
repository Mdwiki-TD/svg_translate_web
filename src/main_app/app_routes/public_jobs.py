"""Public routes for managing background jobs."""

from __future__ import annotations

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

from ..jobs_workers.objects import JobData
from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from ..su_services import load_job_result
from .admin.admins_required import admin_required
from .jobs_routes_utils import (
    cancel_job_handler,
    delete_job_handler,
    job_detail_handler,
    jobs_list_handler,
    start_job_handler,
)

JOBS_BP = "public_jobs"


class JobsPublicRoutes:
    """Jobs management routes."""

    def __init__(self, name: str, jobs_data_infos: dict[str, JobData], url_prefix: str) -> None:
        self.bp = Blueprint(name, __name__, url_prefix=url_prefix)
        self.jobs_data_infos: dict[str, JobData] = jobs_data_infos
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.bp.post("/<string:job_type>/<int:job_id>/cancel")
        def cancel_job(job_type: str, job_id: int) -> Response:
            if job_type not in self.jobs_data_infos:
                flash("Job type not found.", "warning")
                abort(404)
            return cancel_job_handler(job_id, job_type, JOBS_BP)

        @self.bp.get("/<string:job_type>")
        def jobs_list(job_type: str) -> str:
            template_data = self.jobs_data_infos.get(job_type)
            if not template_data:
                abort(404)
            return jobs_list_handler(job_type, template_data, JOBS_BP)

        @self.bp.get("/<string:job_type>/<int:job_id>")
        def job_detail(job_type: str, job_id: int) -> Response | str:
            template_data = self.jobs_data_infos.get(job_type)
            if not template_data:
                abort(404)
            return job_detail_handler(job_id, job_type, template_data, JOBS_BP)

        @self.bp.get("/<string:job_type>/<int:job_id>/expand")
        def job_detail_expand(job_type: str, job_id: int) -> Response | str:
            template_data = self.jobs_data_infos.get(job_type)
            if not template_data:
                abort(404)
            return job_detail_handler(job_id, job_type, template_data, JOBS_BP, expand_all=True)

        @self.bp.post("/<string:job_type>/start")
        def start_job(job_type: str) -> ResponseReturnValue:
            if job_type not in self.jobs_data_infos:
                abort(404)

            job_id = start_job_handler(job_type, request.form.to_dict(), JOBS_BP)
            if not job_id:
                return redirect(url_for(f"{JOBS_BP}.jobs_list", job_type=job_type))
            return redirect(url_for(f"{JOBS_BP}.job_detail", job_type=job_type, job_id=job_id))

        @self.bp.post("/<string:job_type>/<int:job_id>/delete")
        @admin_required
        def delete_job(job_type: str, job_id: int) -> Response:
            if job_type not in self.jobs_data_infos:
                abort(404)
            return delete_job_handler(job_id, job_type, JOBS_BP)

        @self.bp.get("/job-file/<string:result_file>/<string:job_type>")
        def read_job_result_file(result_file: str, job_type: str) -> ResponseReturnValue:
            if job_type not in self.jobs_data_infos:
                abort(404)
            result_data = load_job_result(result_file)
            return jsonify(result_data)


jobs_public_module = JobsPublicRoutes(
    name="public_jobs",
    jobs_data_infos=jobs_data_public,
    url_prefix="/jobs",
)

__all__ = [
    "jobs_public_module",
]
