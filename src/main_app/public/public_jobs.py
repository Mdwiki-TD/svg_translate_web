"""Public routes for managing background jobs."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
)

from ..admin.decorators import admin_required
from ..jobs_workers.objects import JobData
from .auth.decorators import oauth_required
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
            ("/job-file/<string:result_file>/<string:job_type>", "GET", oauth_required(self.read_job_result_file)),
            ("/<string:job_type>/<int:job_id>/cancel", "POST", oauth_required(self.cancel_job)),
            ("/<string:job_type>/start", "POST", oauth_required(self.start_job)),
            ("/<string:job_type>/<int:job_id>/delete", "POST", admin_required(self.delete_job)),
            ("/<string:job_type>/<int:job_id>/mark_as_completed", "POST", admin_required(self.mark_as_completed)),
        ]
        for rule, method, target in routes:
            self.bp.route(rule, methods=[method])(target)

        self.bp.add_url_rule(
            "/<string:job_type>/file/<int:file_number>/<string:list_name>/<int:draw>",
            # endpoint="read_result_file",
            view_func=self.read_result_file,
        )
        self.bp.add_url_rule(
            "/<string:job_type>/file/<int:file_number>/<string:list_name>/<int:draw>/<int:limit>",
            # endpoint="read_result_file",
            view_func=self.read_result_file,
        )

__all__ = [
    "PublicJobsRoutes",
]
