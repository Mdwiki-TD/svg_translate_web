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
    request,
    url_for,
)
from flask.typing import ResponseReturnValue
from flask_wtf import FlaskForm
from werkzeug.wrappers.response import Response

from ..database.exceptions import DuplicateRecordError
from ..database.services import JobsService, SettingsService
from ..io import load_job_result
from ..jobs_workers.jobs_worker import (
    cancel_job_worker,
    start_job_form,
)
from ..jobs_workers.objects import JobData
from ..services.auth.utils import get_current_user
from .utils.routes_utils import can_run_bg_jobs, load_auth_payload

logger = logging.getLogger(__name__)


class SharedJobRoutes:
    def __init__(self) -> None:
        self.job_service = JobsService()
        self.settings_service = SettingsService()

    def can_manage_job(self, job: Any, user: Any) -> bool:
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

    def cancel_job_handler(self, job_id: int, job_type: str) -> str:
        """Cancel a running job."""
        user = get_current_user()
        if not user:
            flash("You must be logged in to cancel jobs.", "danger")
            return "job_detail"

        try:
            job = self.job_service.get_job(job_id, job_type)
        except LookupError:
            flash("Job not found.", "warning")
            return "jobs_list"

        if not self.can_manage_job(job, user):
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

    def start_job_handler(
        self,
        job_type: str,
        args: dict[str, Any],
        check_can_run_bg_jobs: bool = False,
        form_data: dict[str, Any] | None = None,
    ) -> int | None:
        """Start a job."""
        user = get_current_user()

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
            job_id = start_job_form(auth_payload, job_type, args, form_data)
            flash(f"Job {job_id} started to {job_type}.", "success")
            return job_id
        except DuplicateRecordError:
            logger.warning(
                "User '%s' attempted to start duplicate job type '%s'", getattr(user, "username", "N/A"), job_type
            )
            flash("A job of this type is already running. Please wait for it to complete.", "warning")
        except Exception:
            logger.exception("Failed to start job")
            flash("Failed to start job. Please try again.", "danger")

        return None

    def delete_job_handler(self, job_id: int, job_type: str) -> str:
        """Delete a job by ID and job type."""
        user = get_current_user()
        if not user:
            flash("You must be logged in to delete jobs.", "danger")
            return "job_detail"

        try:
            job = self.job_service.get_job(job_id, job_type)
        except LookupError:
            flash("Job not found.", "warning")
            return "jobs_list"

        if not self.can_manage_job(job, user):
            flash("You don't have permission to delete this job.", "danger")
            return "job_detail"

        try:
            if cancel_job_worker(job_id, job_type, job):
                logger.info("Cancelled running job %s before deletion", job_id)

            if self.job_service.delete_job_by_id_and_type(job_id, job_type):
                flash(f"Job {job_id} deleted successfully.", "success")
            else:
                flash(f"Failed to delete job {job_id}", "danger")
        except Exception:
            logger.exception("Failed to delete job")
            flash(f"Failed to delete job {job_id}", "danger")

        return "jobs_list"

    def mark_as_completed_handler(self, job_id: int, job_type: str):
        """Mark job as completed."""
        user = get_current_user()
        if not user:
            flash("You must be logged in to change job stats.", "danger")
            return

        try:
            job = self.job_service.get_job(job_id, job_type)
        except LookupError:
            flash("Job not found.", "warning")
            return

        if not self.can_manage_job(job, user):
            flash("You don't have permission to change job stats.", "danger")
            return

        try:
            self.job_service.mark_as_completed(job)
        except Exception:
            flash(f"Can't mark job {job_id} as completed.", "danger")
            return

        return

    # ================================
    # Jobs handlers
    # ================================

    def jobs_list_handler(self, template_data: JobData, form: Any | None = None) -> str:
        """Render the jobs list dashboard for any job type."""
        try:
            jobs = self.job_service.list_jobs(limit=100, job_type=template_data.job_type)
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Unable to load jobs list.")
            flash("Unable to load jobs list.", "danger")
            jobs: list[Any] = []

        return render_template(
            template_data.job_list_template,
            template_data=template_data,
            form=form,
            jobs=jobs,
        )

    def job_detail_handler(
        self,
        job_id: int,
        template_data: JobData,
        bp_name: str,
        expand_all: bool = False,
    ) -> Response | str:
        """Render the job detail page for any job type."""
        job_type = template_data.job_type

        try:
            job = self.job_service.get_job(job_id, job_type)
        except LookupError:
            logger.error("Job not found: id=%s, type=%s", job_id, job_type)
            flash(f"Job id {job_id} was not found", "warning")
            return redirect(url_for(f"{bp_name}.jobs_list", job_type=job_type))

        # Load job result if available
        result_data = None

        if job.result_file:
            result_data = load_job_result(job.result_file)

        return render_template(
            template_data.job_details_template,
            template_data=template_data,
            job=job,
            result_data=result_data,
            expand_all=expand_all,
            bp_name=bp_name,
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
        self.shared_service = SharedJobRoutes()
        self.settings_service = self.shared_service.settings_service
        self._setup_routes()

    @abstractmethod
    def _setup_routes(self) -> None:
        raise NotImplementedError("This method must be implemented in the subclass")

    def _redirect_to_job_list(self, job_type):
        return redirect(url_for(f"{self.bp_name}.jobs_list", job_type=job_type))

    def _redirect_to_job_detail(self, job_type, job_id):
        return redirect(url_for(f"{self.bp_name}.job_detail", job_type=job_type, job_id=job_id))

    def load_form(self, template_data: JobData) -> FlaskForm:
        all_settings = {}

        if template_data.load_settings:
            all_settings = self.settings_service.get_all_settings_ready()

        form = template_data.form_class(all_settings=all_settings, request_args=request.args)
        return form

    # -----------------------
    # Routes entry points
    # -----------------------
    def cancel_job(self, job_type: str, job_id: int) -> Response:
        if job_type not in self.jobs_data_infos:
            flash("Job type not found.", "warning")
            abort(404)

        result = self.shared_service.cancel_job_handler(job_id, job_type)

        if result == "job_detail":
            return self._redirect_to_job_detail(job_type, job_id)

        return self._redirect_to_job_list(job_type)

    def job_detail(self, job_type: str, job_id: int) -> Response | str:
        # Load template data
        template_data: JobData | None = self.jobs_data_infos.get(job_type)

        if not template_data:
            abort(404)

        # return self.job_details(template_data, job_id)
        return self.shared_service.job_detail_handler(job_id, template_data, bp_name=self.bp_name)

    def job_detail_expand(self, job_type: str, job_id: int) -> Response | str:
        # Load template data
        template_data: JobData | None = self.jobs_data_infos.get(job_type)

        if not template_data:
            abort(404)

        # return self.job_details(template_data, job_id, expand_all=True)
        return self.shared_service.job_detail_handler(job_id, template_data, bp_name=self.bp_name, expand_all=True)

    def delete_job(self, job_type: str, job_id: int) -> Response:
        if job_type not in self.jobs_data_infos:
            abort(404)

        result = self.shared_service.delete_job_handler(job_id, job_type)

        if result == "job_detail":
            return self._redirect_to_job_detail(job_type, job_id)

        return self._redirect_to_job_list(job_type)

    def start_job(self, job_type: str) -> ResponseReturnValue:
        template_data: JobData | None = self.jobs_data_infos.get(job_type)
        if not template_data:
            abort(404)

        form_data = {}

        if template_data.form_class is not None:
            form = self.load_form(template_data)
            if not form.validate_on_submit():
                # return jsonify(form.errors)
                # target = request.referrer or url_for(f"{self.bp_name}.jobs_list", job_type=job_type)
                # return redirect(target)
                return self.shared_service.jobs_list_handler(template_data, form)
            else:
                form_data = form.data

        args = request.form.to_dict()

        job_id = self.shared_service.start_job_handler(job_type, args, form_data=form_data)

        if not job_id:
            return self._redirect_to_job_list(job_type)

        return self._redirect_to_job_detail(job_type, job_id)

    def jobs_list(self, job_type: str) -> str:
        template_data: JobData | None = self.jobs_data_infos.get(job_type)
        if not template_data:
            abort(404)

        form = None
        if template_data.form_class is not None:
            form = self.load_form(template_data)

        return self.shared_service.jobs_list_handler(template_data, form)

    def mark_as_completed(self, job_type: str, job_id: int) -> Response:
        if job_type not in self.jobs_data_infos:
            abort(404)

        self.shared_service.mark_as_completed_handler(job_id, job_type)

        return self._redirect_to_job_detail(job_type, job_id)

    def read_job_result_file(self, result_file: str, job_type: str) -> ResponseReturnValue:
        if job_type not in self.jobs_data_infos:
            abort(404)

        result_data = load_job_result(result_file)
        return jsonify(result_data)

    def read_result_file(
        self,
        file_number: int,
        job_type: str,
        list_name: str = "files_failed",
        draw: int = 0,
        limit: int = 100,
    ) -> ResponseReturnValue:
        """
        http://127.0.0.1:5000/jobs/copy_svg_langs/file/439/files_failed/1
        """
        if job_type not in self.jobs_data_infos:
            abort(404)

        # copy_svg_langs_job_439.json
        result_file = f"{job_type}_job_{file_number}.json"
        result = []

        result_data = load_job_result(result_file)
        list_data = result_data.get(list_name) if result_data else {}

        if list_data:
            result = list_data
            if len(result) > limit:
                result = result[:limit]

        data = {
            "draw": draw,
            "recordsTotal": len(list_data),
            "recordsFiltered": len(result),
            "data": result,
        }

        return jsonify(data)


__all__ = [
    "SharedJobRoutes",
    "JobsBp",
]
