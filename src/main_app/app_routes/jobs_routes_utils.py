"""Shared job route handlers used by both admin and public job blueprints."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from flask import (
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    url_for,
)
from flask.typing import ResponseReturnValue
from werkzeug.wrappers.response import Response

from ..db.exceptions import DuplicateJobError
from ..db.services import (
    delete_job,
    get_job,
    list_jobs,
)
from ..jobs_workers.jobs_worker import (
    cancel_job_worker,
    start_job,
)
from ..jobs_workers.objects import JobData
from ..su_services import load_job_result
from .auth.utils import load_user
from .utils.routes_utils import can_run_bg_jobs, load_auth_payload

logger = logging.getLogger(__name__)


def can_manage_job(job: Any, user: Any) -> bool:
    """Check if the current user can manage (cancel/delete) a job.

    Returns True if the user is an admin (coordinator) or if the user
    is the owner of the job.
    """
    if not user:
        return False
    if getattr(user, "is_active_admin", False):
        return True
    job_username = getattr(job, "username", None)
    if job_username and job_username == user.username:
        return True
    return False


def cancel_job_handler(job_id: int, job_type: str) -> str:
    """Cancel a running job."""
    user = load_user()
    if not user:
        flash("You must be logged in to cancel jobs.", "danger")
        return "job_detail"

    try:
        job = get_job(job_id, job_type)
    except LookupError:
        flash("Job not found.", "warning")
        return "jobs_list"

    if not can_manage_job(job, user):
        flash("You don't have permission to cancel this job.", "danger")
        return "job_detail"

    try:
        if cancel_job_worker(job_id, job_type, job):
            flash(f"Job {job_id} cancellation requested.", "success")
        else:
            flash(f"Job {job_id} is not running or already cancelled.", "warning")
    except Exception:
        logger.exception("Failed to cancel job")
        flash(f"Failed to cancel job {job_id}", "danger")

    return "job_detail"


def delete_job_handler(job_id: int, job_type: str) -> str:
    """Delete a job by ID and job type."""
    user = load_user()
    if not user:
        flash("You must be logged in to delete jobs.", "danger")
        return "job_detail"

    try:
        job = get_job(job_id, job_type)
    except LookupError:
        flash("Job not found.", "warning")
        return "jobs_list"

    if not can_manage_job(job, user):
        flash("You don't have permission to delete this job.", "danger")
        return "job_detail"

    try:
        if cancel_job_worker(job_id, job_type, job):
            logger.info("Cancelled running job %s before deletion", job_id)

        if delete_job(job_id, job_type):
            flash(f"Job {job_id} deleted successfully.", "success")
        else:
            flash(f"Failed to delete job {job_id}", "danger")
    except Exception:
        logger.exception("Failed to delete job")
        flash(f"Failed to delete job {job_id}", "danger")

    return "jobs_list"


def start_job_handler(
    job_type: str,
    args: dict[str, Any],
    check_can_run_bg_jobs: bool = False,
) -> int | None:
    """Start a job."""
    user = load_user()

    if not user:
        flash("You must be logged in to start this job.", "danger")
        return None

    if check_can_run_bg_jobs and not can_run_bg_jobs(user):
        flash("You do not have permission to run background jobs.", "danger")
        return None

    try:
        auth_payload = load_auth_payload(user)
    except Exception:
        logger.exception("Failed to load auth payload")
        flash("Failed to load auth payload. Please try again.", "danger")
        return None

    try:
        job_id = start_job(auth_payload, job_type, args)
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


def jobs_list_handler(job_type: str, template_data: JobData) -> str:
    """Render the jobs list dashboard for any job type."""
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


def job_detail_handler(
    job_id: int,
    job_type: str,
    template_data: JobData,
    bp_name: str,
    expand_all: bool = False,
) -> Response | str:
    """Render the job detail page for any job type."""

    try:
        job = get_job(job_id, job_type)
    except LookupError as exc:
        logger.exception("Job not found")
        flash(str(exc), "warning")
        return redirect(url_for(f"{bp_name}.jobs_list", job_type=job_type))

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


class JobsBp(ABC):
    """Jobs management routes."""

    def __init__(
        self,
        jobs_data_infos: dict[str, JobData],
        bp_name: str,
    ) -> None:
        self.jobs_data_infos: dict[str, JobData] = jobs_data_infos
        self.bp_name = bp_name
        self._setup_routes()

    def cancel_job(self, job_type: str, job_id: int) -> Response:
        if job_type not in self.jobs_data_infos:
            flash("Job type not found.", "warning")
            abort(404)

        result = cancel_job_handler(job_id, job_type)

        if result == "job_detail":
            return redirect(url_for(f"{self.bp_name}.job_detail", job_type=job_type, job_id=job_id))

        return redirect(url_for(f"{self.bp_name}.jobs_list", job_type=job_type))

    def jobs_list(self, job_type: str) -> str:
        template_data: JobData | None = self.jobs_data_infos.get(job_type)
        if not template_data:
            abort(404)

        return jobs_list_handler(job_type, template_data)

    def job_detail(self, job_type: str, job_id: int, expand_all: bool = False) -> Response | str:
        # Load template data
        template_data: JobData | None = self.jobs_data_infos.get(job_type)

        if not template_data:
            abort(404)

        return job_detail_handler(job_id, job_type, template_data, bp_name=self.bp_name, expand_all=expand_all)

    def start_job(self, job_type: str, args: dict[str, Any]) -> ResponseReturnValue:
        if job_type not in self.jobs_data_infos:
            abort(404)

        job_id = start_job_handler(job_type, args)
        if not job_id:
            return redirect(url_for(f"{self.bp_name}.jobs_list", job_type=job_type))

        return redirect(url_for(f"{self.bp_name}.job_detail", job_type=job_type, job_id=job_id))

    def delete_job(self, job_type: str, job_id: int) -> Response:
        if job_type not in self.jobs_data_infos:
            abort(404)
        result = delete_job_handler(job_id, job_type)

        if result == "job_detail":
            return redirect(url_for(f"{self.bp_name}.job_detail", job_type=job_type, job_id=job_id))

        return redirect(url_for(f"{self.bp_name}.jobs_list", job_type=job_type))

    def read_job_result_file(self, result_file: str, job_type: str) -> ResponseReturnValue:
        """ """
        if job_type not in self.jobs_data_infos:
            abort(404)
        result_data = load_job_result(result_file)
        return jsonify(result_data)

    @abstractmethod
    def _setup_routes(self) -> None:
        raise NotImplementedError("This method must be implemented in the subclass")


__all__ = [
    "JobsBp",
    "can_manage_job",
    "cancel_job_handler",
    "delete_job_handler",
    "start_job_handler",
    "jobs_list_handler",
    "job_detail_handler",
]
