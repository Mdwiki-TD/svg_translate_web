"""Public routes for managing background jobs."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    request,
)
from flask.typing import ResponseReturnValue
from werkzeug.wrappers.response import Response

from ..jobs_workers.objects import JobData
from ..jobs_workers.public_jobs_workers.workers_list_public import jobs_data_public
from .admin.admins_required import admin_required
from .auth.utils import user_login_required
from .jobs_routes_utils import JobsBp

logger = logging.getLogger(__name__)


class PublicJobsRoutes(JobsBp):
    """Jobs management routes."""

    def __init__(
        self,
        bp: Blueprint,
        jobs_data_infos: dict[str, JobData],
        bp_name: str,
    ) -> None:
        self.bp = bp
        self.jobs_data_infos: dict[str, JobData] = jobs_data_infos
        self.bp_name = bp_name
        super().__init__(jobs_data_infos, bp_name)

    def _setup_routes(self) -> None:

        @self.bp.post("/<string:job_type>/<int:job_id>/cancel")
        @user_login_required
        def cancel_job(job_type: str, job_id: int) -> Response:
            return self.cancel_job(job_type, job_id)

        @self.bp.get("/<string:job_type>")
        def jobs_list(job_type: str) -> str:
            return self.jobs_list(job_type)

        @self.bp.get("/<string:job_type>/<int:job_id>")
        def job_detail(job_type: str, job_id: int) -> Response | str:
            return self.job_detail(job_type, job_id)

        @self.bp.get("/<string:job_type>/<int:job_id>/expand")
        def job_detail_expand(job_type: str, job_id: int) -> Response | str:
            return self.job_detail(job_type, job_id, expand_all=True)

        @self.bp.post("/<string:job_type>/start")
        @user_login_required
        def start_job(job_type: str) -> ResponseReturnValue:
            args = request.form.to_dict()
            return self.start_job(job_type, args)

        @self.bp.post("/<string:job_type>/<int:job_id>/delete")
        @admin_required
        def delete_job(job_type: str, job_id: int) -> Response:
            return self.delete_job(job_type, job_id)

        @self.bp.get("/job-file/<string:result_file>/<string:job_type>")
        def read_job_result_file(result_file: str, job_type: str) -> ResponseReturnValue:
            return self.read_job_result_file(result_file, job_type)


# Public API module
jobs_public_module = PublicJobsRoutes(
    bp=Blueprint("public_jobs", __name__, url_prefix="/jobs"),
    jobs_data_infos=jobs_data_public,
    bp_name="public_jobs",
)

__all__ = [
    "jobs_public_module",
]
