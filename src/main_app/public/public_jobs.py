"""Public routes for managing background jobs using MethodViews."""

from __future__ import annotations

import logging

from flask import Blueprint

from ..admin.decorators import admin_required
from ..jobs_workers.objects import JobData
from .auth.decorators import oauth_required
from .shared_jobs_routes import (
    CancelJobView,
    DeleteJobView,
    DrawResultFileView,
    JobDetailView,
    JobsListView,
    MarkJobCompletedView,
    ReadJobResultFileView,
    StartJobView,
)

logger = logging.getLogger(__name__)


class PublicJobsRoutes:
    """Registrar class for binding Public Job MethodViews to a Blueprint."""

    def __init__(
        self,
        jobs_data_infos: dict[str, JobData],
        bp_name: str,
    ) -> None:
        self.jobs_data_infos = jobs_data_infos
        self.bp_name = bp_name

    def register(self, bp: Blueprint) -> None:
        """Register public job rules on the provided blueprint with specific route decorators."""
        view_args = (self.jobs_data_infos, self.bp_name)

        bp.add_url_rule(
            "/<string:job_type>",
            view_func=JobsListView.as_view("jobs_list", *view_args),
        )
        bp.add_url_rule(
            "/<string:job_type>/<int:job_id>",
            view_func=JobDetailView.as_view("job_detail", *view_args),
        )
        bp.add_url_rule(
            "/job-file/<string:result_file>/<string:job_type>",
            view_func=oauth_required(ReadJobResultFileView.as_view("read_job_result_file", *view_args)),
        )
        bp.add_url_rule(
            "/<string:job_type>/<int:job_id>/cancel",
            view_func=oauth_required(CancelJobView.as_view("cancel_job", *view_args)),
        )
        bp.add_url_rule(
            "/<string:job_type>/start",
            view_func=oauth_required(StartJobView.as_view("start_job", *view_args)),
        )
        bp.add_url_rule(
            "/<string:job_type>/<int:job_id>/delete",
            view_func=admin_required(DeleteJobView.as_view("delete_job", *view_args)),
        )
        bp.add_url_rule(
            "/<string:job_type>/<int:job_id>/mark_as_completed",
            view_func=admin_required(MarkJobCompletedView.as_view("mark_as_completed", *view_args)),
        )
        bp.add_url_rule(
            "/<string:job_type>/file/<int:file_number>/<string:list_name>",
            view_func=DrawResultFileView.as_view("draw_result_file", *view_args),
        )


__all__ = [
    "PublicJobsRoutes",
]
