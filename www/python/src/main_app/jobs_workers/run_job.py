"""Entry point for running a single job by its database ID.

Used by Toolforge one-off pods: ``flask run-job-id <job_id>``.
"""

from __future__ import annotations

import json
import logging
import signal

from ..database.services import JobsService
from .admin_jobs_workers.workers_list import jobs_data_admins
from .cancel import DbCancelEvent
from .objects import JobsRunner

logger = logging.getLogger(__name__)


def build_job_user(username: str) -> dict | None:
    """Reconstruct the auth_payload dict from the database for a given username.

    Returns the same shape as ``CurrentUser.to_auth_payload()``:
    ``{id, username, access_token, access_secret}``.
    Returns None if the user has no token (deleted or never logged in).
    """
    from ..database.services.users.user_token_service import UserTokenService
    from ..services.auth.token_manager import TokenManager

    token = UserTokenService().get_user_token_by_username(username)
    if token is None:
        return None
    user = TokenManager().get_authenticated_user(token.user_id)
    return user.to_auth_payload() if user else None


def run_job_by_id(job_id: int) -> int:
    """Execute a single job identified by its database ID.

    Called from the ``flask run-job-id`` CLI command inside a Toolforge pod.

    Returns:
        Exit code: 0 = success, 1 = job crashed, 2 = config/not-found error, 3 = auth error.
    """
    svc = JobsService()
    job = svc.get_by(id=job_id)
    if job is None:
        logger.error("Job %s not found", job_id)
        return 2

    if job.status == "cancelled":
        # Cancelled before the pod started
        return 0

    job_data = jobs_data_admins.get(job.job_type)
    if not job_data or not job_data.job_class:
        svc.mark_failed(job, f"unknown job type {job.job_type}")
        return 2

    user = build_job_user(job.username)
    if user is None:
        svc.mark_failed(job, f"no token for user {job.username}")
        return 3

    payload = json.loads(job.payload) if job.payload else {}
    svc.update_job_status(job_id, "running", job_type=job.job_type)

    cancel_event = DbCancelEvent(job_id)
    signal.signal(signal.SIGTERM, lambda *_: cancel_event.set())

    runner_data = JobsRunner(
        job_id=job_id,
        user=user,
        cancel_event=cancel_event,
        args=payload.get("args") or {},
        form_data=payload.get("form_data"),
    )

    try:
        job_data.job_class(runner_data).run()
    except Exception:
        logger.exception("Job %s crashed", job_id)
        job = svc.get_by(id=job_id)
        if job:
            svc.mark_failed(job, "unhandled exception")
        return 1

    # Safety net: if the worker class didn't set a final status, mark completed
    job = svc.get_by(id=job_id)
    if job and job.status in ("pending", "running"):
        svc.mark_as_completed(job)
    return 0


__all__ = [
    "run_job_by_id",
    "build_job_user",
]
