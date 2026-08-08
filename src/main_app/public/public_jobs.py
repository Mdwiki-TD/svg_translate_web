"""Public routes for managing background jobs."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    request,
)
from flask.typing import ResponseReturnValue
from werkzeug.wrappers.response import Response

from ..admin.decorators import admin_required
from ..jobs_workers.objects import JobData
from .auth.utils import user_login_required
from .shared_jobs_routes import JobsBp

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
        routes = [
            ("/<string:job_type>", "GET", self.jobs_list),
            ("/<string:job_type>/<int:job_id>", "GET", self.job_detail),
            ("/<string:job_type>/<int:job_id>/expand", "GET", self.job_detail_expand),
            ("/job-file/<string:result_file>/<string:job_type>", "GET", user_login_required(self.read_job_result_file)),
            ("/<string:job_type>/<int:job_id>/cancel", "POST", user_login_required(self.cancel_job)),
            ("/<string:job_type>/start", "POST", user_login_required(self.start_job)),
            ("/<string:job_type>/<int:job_id>/delete", "POST", admin_required(self.delete_job)),
        ]
        for rule, method, target in routes:
            self.bp.route(rule, methods=[method])(target)

    def cancel_job(self, job_type: str, job_id: int) -> Response:
        return self.cancel_running_job(job_type, job_id)

    def job_detail(self, job_type: str, job_id: int) -> Response | str:
        return self.job_details(job_type, job_id)

    def job_detail_expand(self, job_type: str, job_id: int) -> Response | str:
        return self.job_details(job_type, job_id, expand_all=True)

    def delete_job(self, job_type: str, job_id: int) -> Response:
        return self.delete_job_record(job_type, job_id)

    def read_job_result_file(self, result_file: str, job_type: str) -> ResponseReturnValue:
        return self.read_job_file(result_file, job_type)


    def start_job(self, job_type: str) -> ResponseReturnValue:
        args = request.form.to_dict()
        return self.start_new_job(job_type, args)

    def jobs_list(self, job_type: str) -> str:
        return self.jobs_lists(job_type)


__all__ = [
    "PublicJobsRoutes",
]
