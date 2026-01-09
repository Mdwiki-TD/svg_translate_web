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
from ....routes_utils import load_auth_payload

logger = logging.getLogger("svg_translate")


def _collect_main_files_jobs_list():
    """Render the collect main files jobs list dashboard."""
    user = current_user()
    # Filter jobs to only show collect_main_files type
    all_jobs = jobs_service.list_jobs(limit=100)
    jobs = [job for job in all_jobs if job.job_type == "collect_main_files"]

    return render_template(
        "admins/collect_main_files_jobs.html",
        current_user=user,
        jobs=jobs,
    )


def _collect_main_files_job_detail(job_id: int):
    """Render the collect main files job detail page."""
    user = current_user()

    try:
        job = jobs_service.get_job(job_id)
        # Ensure this is a collect_main_files job
        if job.job_type != "collect_main_files":
            flash(f"Job {job_id} is not a collect main files job.", "warning")
            return redirect(url_for("admin.collect_main_files_jobs_list"))
    except LookupError as exc:
        logger.exception("Job not found")
        flash(str(exc), "warning")
        return redirect(url_for("admin.collect_main_files_jobs_list"))

    # Load job result if available
    result_data = None
    if job.result_file:
        result_data = jobs_service.load_job_result(job.result_file)

    return render_template(
        "admins/collect_main_files_job_detail.html",
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

    return redirect(url_for("admin.collect_main_files_jobs_list"))


def _fix_nested_main_files_jobs_list():
    """Render the fix nested main files jobs list dashboard."""
    user = current_user()
    # Filter jobs to only show fix_nested_main_files type
    all_jobs = jobs_service.list_jobs(limit=100)
    jobs = [job for job in all_jobs if job.job_type == "fix_nested_main_files"]

    return render_template(
        "admins/fix_nested_main_files_jobs.html",
        current_user=user,
        jobs=jobs,
    )


def _fix_nested_main_files_job_detail(job_id: int):
    """Render the fix nested main files job detail page."""
    user = current_user()
    try:
        job = jobs_service.get_job(job_id)
        # Ensure this is a fix_nested_main_files job
        if job.job_type != "fix_nested_main_files":
            flash(f"Job {job_id} is not a fix nested main files job.", "warning")
            return redirect(url_for("admin.fix_nested_main_files_jobs_list"))
    except LookupError as exc:
        logger.exception("Job not found")
        flash(str(exc), "warning")
        return redirect(url_for("admin.fix_nested_main_files_jobs_list"))

    # Load job result if available
    result_data = None
    if job.result_file:
        result_data = jobs_service.load_job_result(job.result_file)

    return render_template(
        "admins/fix_nested_main_files_job_detail.html",
        current_user=user,
        job=job,
        result_data=result_data,
    )


def _start_fix_nested_main_files_job() -> ResponseReturnValue:
    """Start a job to fix nested tags in all template main files."""
    user = current_user()

    if not user:
        flash("You must be logged in to start this job.", "danger")
        return redirect(url_for("admin.fix_nested_main_files_jobs_list"))

    try:
        # Get auth payload for OAuth uploads
        auth_payload = load_auth_payload(user)
        job_id = jobs_worker.start_fix_nested_main_files_job(auth_payload)
        flash(f"Job {job_id} started to fix nested tags in template main files.", "success")
    except Exception:
        logger.exception("Failed to start job")
        flash("Failed to start job. Please try again.", "danger")

    return redirect(url_for("admin.fix_nested_main_files_jobs_list"))


class Jobs:
    """Collect Main Files Jobs management routes."""

    def __init__(self, bp_admin: Blueprint):

        @bp_admin.get("/collect-main-files-jobs")
        @admin_required
        def collect_main_files_jobs_list():
            return _collect_main_files_jobs_list()

        @bp_admin.get("/collect-main-files-jobs/<int:job_id>")
        @admin_required
        def collect_main_files_job_detail(job_id: int):
            return _collect_main_files_job_detail(job_id)

        @bp_admin.post("/collect-main-files-jobs/start")
        @admin_required
        def start_collect_main_files_job() -> ResponseReturnValue:
            return _start_collect_main_files_job()

        @bp_admin.get("/fix-nested-main-files-jobs")
        @admin_required
        def fix_nested_main_files_jobs_list():
            return _fix_nested_main_files_jobs_list()

        @bp_admin.get("/fix-nested-main-files-jobs/<int:job_id>")
        @admin_required
        def fix_nested_main_files_job_detail(job_id: int):
            return _fix_nested_main_files_job_detail(job_id)

        @bp_admin.post("/fix-nested-main-files-jobs/start")
        @admin_required
        def start_fix_nested_main_files_job() -> ResponseReturnValue:
            return _start_fix_nested_main_files_job()
