"""Admin routes for managing background jobs using MethodViews."""

from __future__ import annotations

import logging

from flask import Blueprint

from ...jobs_workers.objects import JobData
from ...public.shared_jobs_routes import (
    CancelJobView,
    DeleteJobView,
    DrawResultFileView,
    JobDetailView,
    JobsListView,
    MarkJobCompletedView,
    ReadJobResultFileView,
    StartJobView,
)
from ..decorators import admin_required

logger = logging.getLogger(__name__)


class AdminJobsRoutes:
    """Registrar class for binding Admin Job MethodViews to a Blueprint."""

    decorators = [admin_required]

    def __init__(
        self,
        jobs_data_infos: dict[str, JobData],
        bp_name: str,
    ) -> None:
        self.jobs_data_infos = jobs_data_infos
        self.bp_name = bp_name

    def register(self, bp: Blueprint) -> None:
        """Register admin job rules on the provided blueprint with admin_required applied."""
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
            view_func=ReadJobResultFileView.as_view("read_job_result_file", *view_args),
        )

        bp.add_url_rule(
            "/<string:job_type>/<int:job_id>/cancel",
            view_func=CancelJobView.as_view("cancel_job", *view_args),
        )

        bp.add_url_rule(
            "/<string:job_type>/start",
            view_func=StartJobView.as_view("start_job", *view_args),
        )

        bp.add_url_rule(
            "/<string:job_type>/<int:job_id>/delete",
            view_func=DeleteJobView.as_view("delete_job", *view_args),
        )

        bp.add_url_rule(
            "/<string:job_type>/<int:job_id>/mark_as_completed",
            view_func=MarkJobCompletedView.as_view("mark_as_completed", *view_args),
        )

        bp.add_url_rule(
            "/<string:job_type>/file/<int:file_number>/<string:list_name>",
            view_func=DrawResultFileView.as_view("draw_result_file", *view_args),
        )


__all__ = [
    "AdminJobsRoutes",
]
