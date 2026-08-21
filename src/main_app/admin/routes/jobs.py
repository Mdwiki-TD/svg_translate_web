"""Admin routes for managing background jobs."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    request,
)

from ...jobs_workers.objects import JobData
from ...public.shared_jobs_routes import JobsBp
from ..decorators import admin_required

logger = logging.getLogger(__name__)


class AdminJobsRoutes(JobsBp):
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

            ("/job-file/<string:result_file>/<string:job_type>", "GET", self.read_job_result_file),

            ("/<string:job_type>/<int:job_id>/cancel", "POST", self.cancel_job),
            ("/<string:job_type>/start", "POST", self.start_job),
            ("/<string:job_type>/<int:job_id>/delete", "POST", self.delete_job),
            ("/<string:job_type>/<int:job_id>/mark_as_completed", "POST", self.mark_as_completed),

            ("/<string:job_type>/file/<int:file_number>/<string:list_name>", "GET", self.draw_result_file),
        ]

        for rule, method, target in routes:
            self.bp.route(rule, methods=[method])(admin_required(target))

__all__ = [
    "AdminJobsRoutes",
]
