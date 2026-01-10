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
from werkzeug.wrappers.response import Response

from .... import jobs_service, jobs_worker
from ....routes_utils import load_auth_payload
from ....users.current import current_user
from ..admins_required import admin_required

logger = logging.getLogger("svg_translate")


def _collect_main_files_jobs_list() -> str:
    """
    Render the collect main files jobs list dashboard.
    """
    user = current_user()
    # Filter jobs at database level for better performance
    jobs = jobs_service.list_jobs(limit=100, job_type="collect_main_files")

    return render_template(
        "admins/collect_main_files_jobs.html",
        current_user=user,
        jobs=jobs,
    )


def _collect_main_files_job_detail(job_id: int) -> Response | str:
    """Render the collect main files job detail page."""
    user = current_user()

    try:
        job = jobs_service.get_job(job_id, "collect_main_files")
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


def _cancel_job(job_id: int, job_type: str) -> Response:
    """Cancel a running job."""
    if jobs_worker.cancel_job(job_id):
        flash(f"Job {job_id} cancellation requested.", "success")
    else:
        flash(f"Job {job_id} is not running or already cancelled.", "warning")

    return redirect(url_for(f"admin.{job_type}_jobs_list"))


def _delete_job(job_id: int, job_type: str) -> Response:
    """Delete a job by ID and job type."""

    try:
        # Cancel the job if it's running
        if jobs_worker.cancel_job(job_id):
            logger.info(f"Cancelled running job {job_id} before deletion")

        jobs_service.delete_job(job_id, job_type)
        flash(f"Job {job_id} deleted successfully.", "success")
    except Exception as exc:
        logger.exception("Failed to delete job")
        flash(f"Failed to delete job {job_id}: {str(exc)}", "danger")

    return redirect(url_for(f"admin.{job_type}_jobs_list"))


def _fix_nested_main_files_jobs_list():
    """
    Render the fix nested main files jobs list dashboard.
    """
    user = current_user()
    # Filter jobs at database level for better performance
    jobs = jobs_service.list_jobs(limit=100, job_type="fix_nested_main_files")

    return render_template(
        "admins/fix_nested_main_files_jobs.html",
        current_user=user,
        jobs=jobs,
    )


def _fix_nested_main_files_job_detail(job_id: int) -> Response | str:
    """Render the fix nested main files job detail page."""
    user = current_user()
    try:
        job = jobs_service.get_job(job_id, "fix_nested_main_files")
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


def _start_collect_main_files_job() -> int:
    """Start a job to collect main files for templates."""
    user = current_user()

    if not user:
        flash("You must be logged in to start this job.", "danger")
        return False

    try:
        # Get auth payload for OAuth uploads
        auth_payload = load_auth_payload(user)
        job_id = jobs_worker.start_collect_main_files_job(auth_payload)
        flash(f"Job {job_id} started to collect main files for templates.", "success")
        return job_id
    except Exception:
        logger.exception("Failed to start job")
        flash("Failed to start job. Please try again.", "danger")

    return False


def _start_fix_nested_main_files_job() -> int:
    """Start a job to fix nested tags in all template main files."""
    user = current_user()

    if not user:
        flash("You must be logged in to start this job.", "danger")
        return False

    try:
        # Get auth payload for OAuth uploads
        auth_payload = load_auth_payload(user)
        job_id = jobs_worker.start_fix_nested_main_files_job(auth_payload)
        flash(f"Job {job_id} started to fix nested tags in template main files.", "success")
        return job_id
    except Exception:
        logger.exception("Failed to start job")
        flash("Failed to start job. Please try again.", "danger")

    return False


class Jobs:
    """Collect Main Files Jobs management routes."""

    def __init__(self, bp_admin: Blueprint) -> None:
        # ================================
        # Collect Main Files Jobs routes
        # ================================

        @bp_admin.get("/collect-main-files")
        @admin_required
        def collect_main_files_jobs_list() -> str:
            return _collect_main_files_jobs_list()

        @bp_admin.get("/collect-main-files/<int:job_id>")
        @admin_required
        def collect_main_files_job_detail(job_id: int) -> Response | str:
            return _collect_main_files_job_detail(job_id)

        @bp_admin.post("/collect-main-files/start")
        @admin_required
        def start_collect_main_files_job() -> ResponseReturnValue:
            job_id = _start_collect_main_files_job()
            if not job_id:
                return redirect(url_for("admin.collect_main_files_jobs_list"))
            return redirect(url_for("admin.collect_main_files_job_detail", job_id=job_id))

        @bp_admin.post("/collect-main-files/<int:job_id>/delete")
        @admin_required
        def delete_collect_main_files_job(job_id: int) -> Response:
            return _delete_job(job_id, "collect_main_files")

        @bp_admin.post("/collect-main-files/<int:job_id>/cancel")
        @admin_required
        def cancel_collect_main_files_job(job_id: int) -> Response:
            return _cancel_job(job_id, "collect_main_files")

        # ================================
        # Fix Nested Main Files Jobs routes
        # ================================

        @bp_admin.get("/fix-nested-main-files")
        @admin_required
        def fix_nested_main_files_jobs_list():
            return _fix_nested_main_files_jobs_list()

        @bp_admin.get("/fix-nested-main-files/<int:job_id>")
        @admin_required
        def fix_nested_main_files_job_detail(job_id: int) -> Response | str:
            return _fix_nested_main_files_job_detail(job_id)

        @bp_admin.post("/fix-nested-main-files/start")
        @admin_required
        def start_fix_nested_main_files_job() -> ResponseReturnValue:
            job_id = _start_fix_nested_main_files_job()
            if not job_id:
                return redirect(url_for("admin.fix_nested_main_files_jobs_list"))
            return redirect(url_for("admin.fix_nested_main_files_job_detail", job_id=job_id))

        @bp_admin.post("/fix-nested-main-files/<int:job_id>/delete")
        @admin_required
        def delete_fix_nested_main_files_job(job_id: int) -> Response:
            return _delete_job(job_id, "fix_nested_main_files")

        @bp_admin.post("/fix-nested-main-files/<int:job_id>/cancel")
        @admin_required
        def cancel_fix_nested_main_files_job(job_id: int) -> Response:
            return _cancel_job(job_id, "fix_nested_main_files")
