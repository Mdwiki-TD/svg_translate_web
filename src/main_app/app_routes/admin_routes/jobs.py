"""Admin routes for managing background jobs."""

from __future__ import annotations

import logging
from typing import Any

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.typing import ResponseReturnValue
from werkzeug.wrappers.response import Response

from ...db.exceptions import DuplicateJobError
from ...db.services import (
    delete_job,
    get_job,
    list_jobs,
)
from ...jobs_workers import jobs_worker
from ...jobs_workers.admin_jobs_workers.workers_list import jobs_data_admins
from ...jobs_workers.objects import JobData
from ...su_services import load_job_result
from ..admin.admins_required import admin_required
from ..auth.utils import load_user
from ..jobs_routes_utils import can_manage_job
from ..utils.routes_utils import load_auth_payload

logger = logging.getLogger(__name__)


def _cancel_job(job_id: int, job_type: str) -> Response:
    """Cancel a running job."""
    user = load_user()
    if not user:
        flash("You must be logged in to cancel jobs.", "danger")
        return redirect(url_for("admin.jobs.job_detail", job_type=job_type, job_id=job_id))

    try:
        job = get_job(job_id, job_type)
    except LookupError:
        flash("Job not found.", "warning")
        return redirect(url_for("admin.jobs.jobs_list", job_type=job_type))

    if not can_manage_job(job, user):
        flash("You don't have permission to cancel this job.", "danger")
        return redirect(url_for("admin.jobs.job_detail", job_type=job_type, job_id=job_id))

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
        logger.warning(
            "User '%s' attempted to start duplicate job type '%s'", getattr(user, "username", "N/A"), job_type
        )
        flash("A job of this type is already running. Please wait for it to complete.", "warning")
    except Exception:
        logger.exception("Failed to start job")
        flash("Failed to start job. Please try again.", "danger")

    return None


# ================================
# Jobs handlers
# ================================


def _jobs_list(job_type: str, template_data: JobData) -> str:
    """Render the jobs list dashboard for any job type."""
    # Filter jobs at database level for better performance
    try:
        jobs = list_jobs(limit=100, job_type=job_type)
    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Unable to load jobs list.")
        flash("Unable to load jobs list.", "danger")
        jobs: list[Any] = []

    template_name = template_data.job_list_template

    return render_template(
        template_name,
        jobs=jobs,
        job_type=job_type,
        list_title=template_data.job_name,
        list_headline=template_data.job_name,
        start_confirm_message=template_data.start_confirm_message,
    )


def _job_detail(
    job_id: int,
    job_type: str,
    template_data: JobData,
    expand_all: bool = False,
) -> Response | str:
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
        result_data = load_job_result(job.result_file)

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
    """Jobs management routes."""

    def __init__(self, name: str, jobs_data_infos: dict[str, JobData]) -> None:
        self.bp = Blueprint(name, __name__, url_prefix="/jobs")
        self.jobs_data_infos: dict[str, JobData] = jobs_data_infos
        self._setup_routes()

    def _setup_routes(self) -> None:
        # ================================
        # Cancel Jobs routes
        # ================================

        @self.bp.post("/<string:job_type>/<int:job_id>/cancel")
        @admin_required
        def cancel_job(job_type: str, job_id: int) -> Response:
            if job_type not in self.jobs_data_infos:
                flash("Job type not found.", "warning")
                return abort(404)

            return _cancel_job(job_id, job_type)

        # ================================
        # Jobs List routes
        # ================================

        @self.bp.get("/<string:job_type>")
        @admin_required
        def jobs_list(job_type: str) -> str:
            template_data: JobData | None = self.jobs_data_infos.get(job_type)
            if not template_data:
                return abort(404)

            return _jobs_list(job_type, template_data)

        # ================================
        # Job Detail routes
        # ================================

        @self.bp.get("/<string:job_type>/<int:job_id>")
        @admin_required
        def job_detail(job_type: str, job_id: int) -> Response | str:
            # Load template data
            template_data: JobData | None = self.jobs_data_infos.get(job_type)

            if not template_data:
                return abort(404)

            return _job_detail(job_id, job_type, template_data)

        @self.bp.get("/<string:job_type>/<int:job_id>/expand")
        @admin_required
        def job_detail_expand(job_type: str, job_id: int) -> Response | str:
            # Load template data
            template_data: JobData | None = self.jobs_data_infos.get(job_type)

            if not template_data:
                return abort(404)

            return _job_detail(job_id, job_type, template_data, expand_all=True)

        # ================================
        # Start Job routes
        # ================================

        @self.bp.post("/<string:job_type>/start")
        @admin_required
        def start_job(job_type: str) -> ResponseReturnValue:
            if job_type not in self.jobs_data_infos:
                return abort(404)

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
            if job_type not in self.jobs_data_infos:
                return abort(404)
            return _delete_job(job_id, job_type)

        @self.bp.get("/job-file/<string:result_file>")
        @self.bp.get("/job-file/<string:result_file>/<string:job_type>")
        @admin_required
        def read_job_result_file(result_file: str, job_type: str = "") -> ResponseReturnValue:
            """ """
            if job_type not in self.jobs_data_infos:
                return abort(404)
            result_data = load_job_result(result_file)
            return jsonify(result_data)


# Public API module
jobs_module = Jobs(
    name="jobs",
    jobs_data_infos=jobs_data_admins,
)

__all__ = [
    "jobs_module",
]
