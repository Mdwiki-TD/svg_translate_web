"""Admin routes for managing background jobs."""

from __future__ import annotations

import logging

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    url_for,
)
from flask.typing import ResponseReturnValue
from werkzeug.wrappers.response import Response

from ....config import settings
from ....admins.admins_required import admin_required
from ....jobs_workers import jobs_service, jobs_worker
from ....routes_utils import load_auth_payload
from ....users.current import current_user

logger = logging.getLogger("svg_translate")


def _cancel_job(job_id: int, job_type: str) -> Response:
    """Cancel a running job."""
    if jobs_worker.cancel_job(job_id):
        flash(f"Job {job_id} cancellation requested.", "success")
    else:
        flash(f"Job {job_id} is not running or already cancelled.", "warning")

    return redirect(url_for("admin.jobs_list", job_type=job_type))


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

    return redirect(url_for("admin.jobs_list", job_type=job_type))


def _start_job(job_type: str) -> int:
    """Start a job."""
    user = current_user()

    if not user:
        flash("You must be logged in to start this job.", "danger")
        return False

    try:
        # Get auth payload for OAuth uploads
        auth_payload = load_auth_payload(user)
        job_id = jobs_worker.start_job(auth_payload, job_type)
        flash(f"Job {job_id} started to {job_type.replace('_', ' ')}.", "success")
        return job_id
    except Exception:
        logger.exception("Failed to start job")
        flash("Failed to start job. Please try again.", "danger")

    return False

# ================================
# Collect Main Files Jobs handlers
# ================================


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


def _download_main_files_jobs_list() -> str:
    """
    Render the download main files jobs list dashboard.
    """
    user = current_user()
    # Filter jobs at database level for better performance
    jobs = jobs_service.list_jobs(limit=100, job_type="download_main_files")

    return render_template(
        "admins/download_main_files_jobs.html",
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
        return redirect(url_for("admin.jobs_list", job_type="collect_main_files"))

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

# ================================
# Fix Nested Main Files Jobs handlers
# ================================


def _fix_nested_main_files_job_detail(job_id: int) -> Response | str:
    """Render the fix nested main files job detail page."""
    user = current_user()
    try:
        job = jobs_service.get_job(job_id, "fix_nested_main_files")
    except LookupError as exc:
        logger.exception("Job not found")
        flash(str(exc), "warning")
        return redirect(url_for("admin.jobs_list", job_type="fix_nested_main_files"))

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

# ================================
# Download Main Files Jobs handlers
# ================================


def _download_main_files_job_detail(job_id: int) -> Response | str:
    """Render the download main files job detail page."""
    user = current_user()

    try:
        job = jobs_service.get_job(job_id, "download_main_files")
    except LookupError as exc:
        logger.exception("Job not found")
        flash(str(exc), "warning")
        return redirect(url_for("admin.jobs_list", job_type="download_main_files"))

    # Load job result if available
    result_data = None
    if job.result_file:
        result_data = jobs_service.load_job_result(job.result_file)

    return render_template(
        "admins/download_main_files_job_detail.html",
        current_user=user,
        job=job,
        result_data=result_data,
    )


class Jobs:
    """Collect Main Files Jobs management routes."""

    def __init__(self, bp_admin: Blueprint) -> None:
        # ================================
        # Cancel Jobs routes
        # ================================

        @bp_admin.post("/<string:job_type>/<int:job_id>/cancel")
        @admin_required
        def cancel_job(job_type: str, job_id: int) -> Response:
            return _cancel_job(job_id, job_type)

        # ================================
        # Jobs List routes
        # ================================

        @bp_admin.get("/<string:job_type>/list")
        @admin_required
        def jobs_list(job_type: str) -> str:
            if job_type == "collect_main_files":
                return _collect_main_files_jobs_list()
            elif job_type == "fix_nested_main_files":
                return _fix_nested_main_files_jobs_list()
            elif job_type == "download_main_files":
                return _download_main_files_jobs_list()
            else:
                abort(404)

        # ================================
        # Collect Main Files Jobs routes
        # ================================

        @bp_admin.get("/collect-main-files/<int:job_id>")
        @admin_required
        def collect_main_files_job_detail(job_id: int) -> Response | str:
            return _collect_main_files_job_detail(job_id)

        @bp_admin.post("/collect-main-files/start")
        @admin_required
        def start_collect_main_files_job() -> ResponseReturnValue:
            job_id = _start_job("collect_main_files")
            if not job_id:
                return redirect(url_for("admin.jobs_list", job_type="collect_main_files"))
            return redirect(url_for("admin.collect_main_files_job_detail", job_id=job_id))

        @bp_admin.post("/collect-main-files/<int:job_id>/delete")
        @admin_required
        def delete_collect_main_files_job(job_id: int) -> Response:
            return _delete_job(job_id, "collect_main_files")

        # ================================
        # Fix Nested Main Files Jobs routes
        # ================================

        @bp_admin.get("/fix-nested-main-files/<int:job_id>")
        @admin_required
        def fix_nested_main_files_job_detail(job_id: int) -> Response | str:
            return _fix_nested_main_files_job_detail(job_id)

        @bp_admin.post("/fix-nested-main-files/start")
        @admin_required
        def start_fix_nested_main_files_job() -> ResponseReturnValue:
            job_id = _start_job("fix_nested_main_files")
            if not job_id:
                return redirect(url_for("admin.jobs_list", job_type="fix_nested_main_files"))
            return redirect(url_for("admin.fix_nested_main_files_job_detail", job_id=job_id))

        @bp_admin.post("/fix-nested-main-files/<int:job_id>/delete")
        @admin_required
        def delete_fix_nested_main_files_job(job_id: int) -> Response:
            return _delete_job(job_id, "fix_nested_main_files")

        # ================================
        # Download Main Files Jobs routes
        # ================================

        @bp_admin.get("/download-main-files/<int:job_id>")
        @admin_required
        def download_main_files_job_detail(job_id: int) -> Response | str:
            return _download_main_files_job_detail(job_id)

        @bp_admin.post("/download-main-files/start")
        @admin_required
        def start_download_main_files_job() -> ResponseReturnValue:
            job_id = _start_job("download_main_files")
            if not job_id:
                return redirect(url_for("admin.jobs_list", job_type="download_main_files"))
            return redirect(url_for("admin.download_main_files_job_detail", job_id=job_id))

        @bp_admin.post("/download-main-files/<int:job_id>/delete")
        @admin_required
        def delete_download_main_files_job(job_id: int) -> Response:
            return _delete_job(job_id, "download_main_files")

        @bp_admin.get("/download-main-files/file/<path:filename>")
        @admin_required
        def serve_download_main_file(filename: str) -> Response:
            """Serve a downloaded main file from the main_files_path directory."""
            from flask import send_from_directory

            return send_from_directory(settings.paths.main_files_path, filename)

        @bp_admin.get("/download-main-files/download-all")
        @admin_required
        def download_all_main_files() -> Response:
            """Download all main files as a zip archive."""
            import io
            import zipfile
            from pathlib import Path

            from flask import send_file

            main_files_path = Path(settings.paths.main_files_path)

            if not main_files_path.exists():
                return "Main files directory does not exist", 404

            # Create a zip file in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in main_files_path.iterdir():
                    if file_path.is_file():
                        zip_file.write(file_path, file_path.name)

            zip_buffer.seek(0)

            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name='main_files.zip'
            )
