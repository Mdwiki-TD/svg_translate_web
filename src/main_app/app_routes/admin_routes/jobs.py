"""Admin routes for managing background jobs."""

from __future__ import annotations

import copy
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
from ...db.exceptions import DuplicateJobError
from ...db.services import (
    delete_job,
    get_job,
    list_jobs,
)
from ...jobs_workers import jobs_worker
from ...jobs_workers.admin_jobs_workers.download_main_files.worker import create_main_files_zip
from ...jobs_workers.admin_jobs_workers.workers_list import jobs_data
from ...su_services import load_job_result, save_job_result_by_name
from ..admin.admins_required import admin_required
from ..auth.utils import load_user
from ..utils.routes_utils import load_auth_payload
from .results_utils import fix_result_data

logger = logging.getLogger(__name__)


def _can_manage_job(job: Any, user: Any) -> bool:
    """Check if the current user can manage (cancel/delete) a job.

    Returns True if the user is an admin (coordinator) or if the user
    is the owner of the job.
    """
    if not user:
        return False
    if getattr(user, "is_active_admin", False):
        return True
    if job.username and job.username == user.username:
        return True
    return False


def load_job_result_and_fix(result_file: str, job_type: str) -> dict[str, Any] | None:
    data = load_job_result(result_file)
    if data:
        data_before = copy.deepcopy(data)
        data2 = fix_result_data(data, job_type)
        if data2 != data_before:
            logger.info(f"Job result {result_file} was fixed")
            save_job_result_by_name(result_file, data2)
        else:
            logger.info(f"Job result {result_file} was not fixed")
        return data2

    return data


def _cancel_job(job_id: int, job_type: str) -> Response:
    """Cancel a running job."""
    user = load_user()
    if not user:
        flash("You must be logged in to cancel jobs.", "danger")
        return redirect(url_for("new_jobs.job_detail", job_type=job_type, job_id=job_id))

    try:
        job = get_job(job_id, job_type)
    except LookupError:
        flash("Job not found.", "warning")
        return redirect(url_for("new_jobs.jobs_list", job_type=job_type))

    if not _can_manage_job(job, user):
        flash("You don't have permission to cancel this job.", "danger")
        return redirect(url_for("new_jobs.job_detail", job_type=job_type, job_id=job_id))

    if jobs_worker.cancel_job_worker(job_id, job_type, job):
        flash(f"Job {job_id} cancellation requested.", "success")
    else:
        flash(f"Job {job_id} is not running or already cancelled.", "warning")

    return redirect(url_for("admin.jobs.job_detail", job_type=job_type, job_id=job_id))


def _delete_job(job_id: int, job_type: str) -> Response:
    """Delete a job by ID and job type."""

    try:
        # Cancel the job if it's running
        if jobs_worker.cancel_job_worker(job_id, job_type):
            logger.info(f"Cancelled running job {job_id} before deletion")

        if delete_job(job_id, job_type):
            flash(f"Job {job_id} deleted successfully.", "success")
        else:
            flash(f"Failed to delete job {job_id}", "danger")
    except Exception:
        logger.exception("Failed to delete job")
        flash(f"Failed to delete job {job_id}", "danger")

    return redirect(url_for("admin.jobs.jobs_list", job_type=job_type))


def _start_job(job_type: str, args: dict[str, Any]) -> int | None:
    """Start a job."""
    user = load_user()

    if not user:
        flash("You must be logged in to start this job.", "danger")
        return None

    try:
        # Get auth payload for OAuth uploads
        auth_payload = load_auth_payload(user)
    except Exception:
        logger.exception("Failed to load auth payload")
        flash("Failed to load auth payload. Please try again.", "danger")
        return None

    try:
        job_id = jobs_worker.start_job(auth_payload, job_type, args)
        flash(f"Job {job_id} started to {job_type}.", "success")
        return job_id
    except DuplicateJobError:
        logger.warning("User '%s' attempted to start duplicate job type '%s'", user.username, job_type)
        flash("A job of this type is already running. Please wait for it to complete.", "warning")
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
    try:
        jobs = list_jobs(limit=100, job_type=job_type)
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to load jobs list.")
        flash("Unable to load jobs list.", "danger")
        jobs = []

    template_data = jobs_data.get(job_type)

    if not template_data:
        abort(404)

    template_name = template_data.job_list_template

    return render_template(
        template_name,
        jobs=jobs,
        job_type=job_type,
        list_title=template_data.job_name,
        list_headline=template_data.job_name,
        start_confirm_message=template_data.start_confirm_message,
    )


def _job_detail(job_id: int, job_type: str, expand_all: bool = False) -> Response | str:
    """Render the job detail page for any job type."""

    try:
        job = get_job(job_id, job_type)
    except LookupError as exc:
        logger.exception("Job not found")
        flash(str(exc), "warning")
        return redirect(url_for("admin.jobs.jobs_list", job_type=job_type))

    # Load job result if available
    result_data = None
    if job.result_file:
        result_data = load_job_result_and_fix(job.result_file, job_type)

    # Load template data
    template_data = jobs_data.get(job_type)

    if not template_data:
        abort(404)

    template_name = template_data.job_details_template

    return render_template(
        template_name,
        job=job,
        job_type=job_type,
        result_data=result_data,
        detail_title=template_data.job_name,
        detail_headline=template_data.job_name,
        expand_all=expand_all,
    )


class Jobs:
    """Collect Templates data Jobs management routes."""

    def __init__(self):
        self.bp = Blueprint("jobs", __name__, url_prefix="/jobs")
        self._setup_routes()

    def _setup_routes(self):

        # ================================
        # Cancel Jobs routes
        # ================================

        @self.bp.post("/<string:job_type>/<int:job_id>/cancel")
        @admin_required
        def cancel_job(job_type: str, job_id: int) -> Response:
            if job_type not in jobs_data:
                abort(404)
            return _cancel_job(job_id, job_type)

        # ================================
        # Jobs List routes
        # ================================

        @self.bp.get("/<string:job_type>")
        @admin_required
        def jobs_list(job_type: str) -> str:
            return _jobs_list(job_type)

        # ================================
        # Job Detail routes
        # ================================

        @self.bp.get("/<string:job_type>/<int:job_id>")
        @admin_required
        def job_detail(job_type: str, job_id: int) -> Response | str:
            return _job_detail(job_id, job_type)

        @self.bp.get("/<string:job_type>/<int:job_id>/expand")
        @admin_required
        def job_detail_expand(job_type: str, job_id: int) -> Response | str:
            return _job_detail(job_id, job_type, expand_all=True)

        # ================================
        # Start Job routes
        # ================================

        @self.bp.post("/<string:job_type>/start")
        @admin_required
        def start_job(job_type: str) -> ResponseReturnValue:
            if job_type not in jobs_data:
                abort(404)

            args = request.form.to_dict()

            job_id = _start_job(job_type, args)
            if not job_id:
                return redirect(url_for("admin.jobs.jobs_list", job_type=job_type))

            return redirect(url_for("admin.jobs.job_detail", job_type=job_type, job_id=job_id))

        # ================================
        # Delete Job routes
        # ================================

        @self.bp.post("/<string:job_type>/<int:job_id>/delete")
        @admin_required
        def delete_job(job_type: str, job_id: int) -> Response:
            if job_type not in jobs_data:
                abort(404)
            return _delete_job(job_id, job_type)

        # ================================
        # download-main-files routes
        # ================================

        @self.bp.get("/download-main-files/file/<str:filename>")
        @admin_required
        def serve_download_main_file(filename: str) -> Response:
            """
            Serve a downloaded main file from the main_files_path directory.
            """
            response = send_from_directory(settings.paths.main_files_path, filename)
            response.headers["Content-Security-Policy"] = "script-src 'none'; object-src 'none'"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response

        @self.bp.get("/download-main-files/download-all")
        @admin_required
        def download_all_main_files() -> ResponseReturnValue:
            """Download all main files as a zip archive."""

            response, status_code = create_main_files_zip()

            # If the response is an error message (not a file), flash it and redirect
            if status_code != 200:
                flash(response, "warning" if status_code == 404 else "danger")
                return redirect(url_for("admin.jobs.jobs_list", job_type="download_main_files"))

            return response

        # ================================
        # crop-main-files routes
        # ================================

        @self.bp.get("/crop-main-files/original/<str:filename>")
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

        @self.bp.get("/crop-main-files/cropped/<str:filename>")
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

        @self.bp.get("/crop-main-files/compare/<str:original>/<str:cropped>")
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

        @self.bp.get("/read-job-result-file/<str:result_file>")
        @self.bp.get("/read-job-result-file/<str:result_file>/<string:job_type>")
        @admin_required
        def read_job_result_file(result_file: str, job_type: str = "") -> ResponseReturnValue:
            """ """
            result_data = load_job_result_and_fix(result_file, job_type)
            return jsonify(result_data)


jobs_module = Jobs()

__all__ = [
    "jobs_module",
]
