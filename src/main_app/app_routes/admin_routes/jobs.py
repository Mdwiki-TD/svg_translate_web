"""Admin routes for managing background jobs."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask.typing import ResponseReturnValue
from werkzeug.wrappers.response import Response

from ...config import settings
from ...jobs_workers import jobs_worker
from ...jobs_workers.download_main_files_worker import create_main_files_zip
from ...jobs_workers.workers_list import JOB_TYPE_LIST_TEMPLATES, JOB_TYPE_TEMPLATES
from ...services import jobs_service
from ...services.users_service import current_user
from ..admin.admins_required import admin_required
from ..utils.routes_utils import load_auth_payload

logger = logging.getLogger(__name__)


def _cancel_job(job_id: int, job_type: str) -> Response:
    """Cancel a running job."""
    if jobs_worker.cancel_job(job_id, job_type):
        flash(f"Job {job_id} cancellation requested.", "success")
    else:
        flash(f"Job {job_id} is not running or already cancelled.", "warning")

    return redirect(url_for("admin.jobs_list", job_type=job_type))


def _delete_job(job_id: int, job_type: str) -> Response:
    """Delete a job by ID and job type."""

    try:
        # Cancel the job if it's running
        if jobs_worker.cancel_job(job_id, job_type):
            logger.info(f"Cancelled running job {job_id} before deletion")

        jobs_service.delete_job(job_id, job_type)
        flash(f"Job {job_id} deleted successfully.", "success")
    except Exception as exc:
        logger.exception("Failed to delete job")
        flash(f"Failed to delete job {job_id}: {str(exc)}", "danger")

    return redirect(url_for("admin.jobs_list", job_type=job_type))


def _start_job(job_type: str) -> int | None:
    """Start a job."""
    user = current_user()

    if not user:
        flash("You must be logged in to start this job.", "danger")
        return None

    try:
        # Get auth payload for OAuth uploads
        auth_payload = load_auth_payload(user)
        job_id = jobs_worker.start_job(auth_payload, job_type)
        flash(f"Job {job_id} started to {job_type.replace('_', ' ')}.", "success")
        return job_id
    except Exception:
        logger.exception("Failed to start job")
        flash("Failed to start job. Please try again.", "danger")

    return None


def _start_job_with_args(job_type: str, args: dict[str, Any]) -> int | None:
    """Start a job."""
    user = current_user()

    if not user:
        flash("You must be logged in to start this job.", "danger")
        return None

    try:
        # Get auth payload for OAuth uploads
        auth_payload = load_auth_payload(user)
        job_id = jobs_worker.start_job_with_args(auth_payload, job_type, args)
        flash(f"Job {job_id} started to {job_type.replace('_', ' ')}.", "success")
        return job_id
    except Exception:
        logger.exception("Failed to start job")
        flash("Failed to start job. Please try again.", "danger")

    return None


# ================================
# Jobs handlers
# ================================


def _jobs_list(job_type: str) -> str:
    """Render the jobs list dashboard for any job type."""
    # Filter jobs at database level for better performance
    jobs = jobs_service.list_jobs(limit=100, job_type=job_type)

    # sort jobs by created_at key
    if jobs:
        jobs = sorted(jobs, key=lambda x: x.created_at or "", reverse=True)

    template = JOB_TYPE_LIST_TEMPLATES.get(job_type)
    if not template:
        abort(404)

    return render_template(
        template,
        jobs=jobs,
        job_type=job_type,
    )


def _job_detail(job_id: int, job_type: str) -> Response | str:
    """Render the job detail page for any job type."""

    try:
        job = jobs_service.get_job(job_id, job_type)
    except LookupError as exc:
        logger.exception("Job not found")
        flash(str(exc), "warning")
        return redirect(url_for("admin.jobs_list", job_type=job_type))

    # Load job result if available
    result_data = None
    if job.result_file:
        result_data = jobs_service.load_job_result(job.result_file)

    template = JOB_TYPE_TEMPLATES.get(job_type)
    if not template:
        abort(404)

    return render_template(
        template,
        job=job,
        job_type=job_type,
        result_data=result_data,
    )


class Jobs:
    """Collect Templates data Jobs management routes."""

    def __init__(self, bp_admin: Blueprint) -> None:
        # ================================
        # Cancel Jobs routes
        # ================================

        @bp_admin.post("/<string:job_type>/<int:job_id>/cancel")
        @admin_required
        def cancel_job(job_type: str, job_id: int) -> Response:
            if job_type not in JOB_TYPE_TEMPLATES:
                abort(404)
            return _cancel_job(job_id, job_type)

        # ================================
        # Jobs List routes
        # ================================

        @bp_admin.get("/<string:job_type>/list")
        @admin_required
        def jobs_list(job_type: str) -> str:
            return _jobs_list(job_type)

        # ================================
        # Job Detail routes
        # ================================

        @bp_admin.get("/<string:job_type>/<int:job_id>")
        @admin_required
        def job_detail(job_type: str, job_id: int) -> Response | str:
            return _job_detail(job_id, job_type)

        # ================================
        # Start Job routes
        # ================================

        @bp_admin.post("/<string:job_type>/start")
        @admin_required
        def start_job(job_type: str) -> ResponseReturnValue:
            if job_type not in JOB_TYPE_TEMPLATES:
                abort(404)
            job_id = _start_job(job_type)
            if not job_id:
                return redirect(url_for("admin.jobs_list", job_type=job_type))
            return redirect(url_for("admin.job_detail", job_type=job_type, job_id=job_id))

        @bp_admin.post("/<string:job_type>/start_with_args")
        @admin_required
        def start_job_with_args(job_type: str) -> ResponseReturnValue:
            if job_type not in JOB_TYPE_TEMPLATES:
                abort(404)

            args = request.form.to_dict()
            job_id = _start_job_with_args(job_type, args)
            if not job_id:
                return redirect(url_for("admin.jobs_list", job_type=job_type))
            return redirect(url_for("admin.job_detail", job_type=job_type, job_id=job_id))

        # ================================
        # Delete Job routes
        # ================================

        @bp_admin.post("/<string:job_type>/<int:job_id>/delete")
        @admin_required
        def delete_job(job_type: str, job_id: int) -> Response:
            if job_type not in JOB_TYPE_TEMPLATES:
                abort(404)
            return _delete_job(job_id, job_type)

        # ================================
        # download-main-files routes
        # ================================

        @bp_admin.get("/download-main-files/file/<path:filename>")
        @admin_required
        def serve_download_main_file(filename: str) -> Response:
            """
            Serve a downloaded main file from the main_files_path directory.
            """
            response = send_from_directory(settings.paths.main_files_path, filename)
            response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response

        @bp_admin.get("/download-main-files/download-all")
        @admin_required
        def download_all_main_files() -> ResponseReturnValue:
            """Download all main files as a zip archive."""

            response, status_code = create_main_files_zip()

            # If the response is an error message (not a file), flash it and redirect
            if status_code != 200:
                flash(response, "warning" if status_code == 404 else "danger")
                return redirect(url_for("admin.jobs_list", job_type="download_main_files"))

            return response

        # ================================
        # crop-main-files routes
        # ================================

        @bp_admin.get("/crop-main-files/original/<path:filename>")
        @admin_required
        def serve_crop_original_file(filename: str) -> Response:
            """
            Serve an original file from the crop_main_files_path/original directory.
            """
            filename = filename.removeprefix("File:")
            response = send_from_directory(Path(settings.paths.crop_main_files_path) / "original", filename)
            response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response

        @bp_admin.get("/crop-main-files/cropped/<path:filename>")
        @admin_required
        def serve_crop_cropped_file(filename: str) -> Response:
            """
            Serve a cropped file from the crop_main_files_path/cropped directory.
            """
            filename = filename.removeprefix("File:")
            response = send_from_directory(Path(settings.paths.crop_main_files_path) / "cropped", filename)
            response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response

        @bp_admin.get("/crop-main-files/compare/<path:original>/<path:cropped>")
        @admin_required
        def compare_crop_files(original: str, cropped: str) -> ResponseReturnValue:
            """Compare crop files"""

            original = original.removeprefix("File:")
            cropped = cropped.removeprefix("File:")
            return render_template(
                "admins/compare_crop_files.html",
                file_original=original,
                file_cropped=cropped,
            )

        @bp_admin.get("/read-job-result-file/<path:result_file>")
        @admin_required
        def read_job_result_file(result_file: str) -> ResponseReturnValue:
            """ """
            result_data = jobs_service.load_job_result(result_file)
            return jsonify(result_data)
