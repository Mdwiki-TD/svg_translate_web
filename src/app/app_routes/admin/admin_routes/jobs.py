"""Admin routes for managing background jobs."""

from __future__ import annotations

import logging
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask.typing import ResponseReturnValue

from ....users.current import current_user
from .... import jobs_service
from .... import jobs_worker
from ..admins_required import admin_required

logger = logging.getLogger("svg_translate")


def _jobs_list():
    """Render the jobs list dashboard."""
    user = current_user()
    jobs = jobs_service.list_jobs(limit=100)
    
    return render_template(
        "admins/jobs.html",
        current_user=user,
        jobs=jobs,
    )


def _job_detail(job_id: int):
    """Render the job detail page."""
    user = current_user()
    
    try:
        job = jobs_service.get_job(job_id)
    except LookupError as exc:
        logger.exception("Job not found")
        flash(str(exc), "warning")
        return redirect(url_for("admin.jobs_list"))
    
    # Load job result if available
    result_data = None
    if job.result_file:
        result_data = jobs_service.load_job_result(job.result_file)
    
    return render_template(
        "admins/job_detail.html",
        current_user=user,
        job=job,
        result_data=result_data,
    )


def _start_collect_main_files_job() -> ResponseReturnValue:
    """Start a job to collect main files for templates."""
    try:
        job_id = jobs_worker.start_collect_main_files_job()
        flash(f"Job {job_id} started to collect main files for templates.", "success")
    except Exception:
        logger.exception("Failed to start job")
        flash("Failed to start job. Please try again.", "danger")
    
    return redirect(url_for("admin.jobs_list"))


class Jobs:
    """Jobs management routes."""
    
    def __init__(self, bp_admin: Blueprint):
        
        @bp_admin.get("/jobs")
        @admin_required
        def jobs_list():
            return _jobs_list()
        
        @bp_admin.get("/jobs/<int:job_id>")
        @admin_required
        def job_detail(job_id: int):
            return _job_detail(job_id)
        
        @bp_admin.post("/jobs/collect-main-files")
        @admin_required
        def start_collect_main_files_job() -> ResponseReturnValue:
            return _start_collect_main_files_job()
