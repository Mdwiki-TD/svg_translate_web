"""Worker module for managing background jobs."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from flask import Flask, current_app

from ..database.exceptions import DuplicateRecordError
from ..database.models import JobRecord
from ..database.services import (
    JobsService,
    SettingsService,
)
from ..io.jobs_files_service import create_cancel_file
from .admin_jobs_workers.workers_list import jobs_data_admins
from .backends.thread_backend import ThreadBackend
from .cancel_registry import (
    get_cancel_event,
    pop_cancel_event,
)
from .objects import JobData, JobsRunner
from .public_jobs_workers.workers_list_public import jobs_data_public

logger = logging.getLogger(__name__)


def load_job_data(job_type) -> JobData | None:
    return jobs_data_admins.get(job_type) or jobs_data_public.get(job_type)


def _load_job_args(job_args: list[dict[str, str]]) -> dict[str, Any]:
    if not job_args:
        return {}

    settings_ready = SettingsService().get_all_settings_ready()
    _args: dict[str, Any] = {}

    for item in job_args:
        key = item["key"]
        key_as = item["as"]
        arg_value = settings_ready.get(key)
        if arg_value is not None:
            _args[key_as] = arg_value

    return _args


def _runner(
    runner_data: JobsRunner,
    target_class: Callable[[JobsRunner]],
    flask_app: Flask,
) -> None:
    """Run a job in a thread with proper exception handling."""
    with flask_app.app_context():
        try:
            worker = target_class(runner_data)
            worker.run()
        finally:
            pop_cancel_event(runner_data.job_id)


def cancel_job_worker(
    job_id: int,
    job_type: str | None = None,
    job: JobRecord | None = None,
) -> bool:
    """
    Cancel a running job.
    Works across multiple processes by updating the database status.
    Returns True if the job was found and cancellation was requested.
    """
    svc = JobsService()
    # if job is None: job = svc.get_by(id=job_id)

    # 1. Try local cancellation (if the job is in this process)
    cancel_event = get_cancel_event(job_id)
    local_cancelled = False
    if cancel_event:
        cancel_event.set()
        logger.info(f"Local cancellation requested for job {job_id}")
        local_cancelled = True

    cancelled_file = None
    # 2. Create result_file_cancelled file
    if job and job.result_file:
        cancelled_file = create_cancel_file(f"{job.result_file}.cancelled")

    # 3. Persist cancellation to DB (for cross-process detection)
    try:
        db_cancelled = svc.cancel_job_db(job_id, job_type)
        if db_cancelled:
            logger.info(f"Database cancellation requested for job {job_id}")

    except Exception:  # pragma: no cover - defensive guard
        logger.exception("Failed to cancel job %s in database.", job_id)
        db_cancelled = False

    return local_cancelled or cancelled_file is not None or db_cancelled


def _sanitize_args(args: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive or unnecessary keys from args before storing."""
    cleaned = dict(args)
    cleaned.pop("csrf_token", None)
    return cleaned


def _start_job_impl(
    auth_payload: dict[str, Any] | None,
    job_type: str,
    args: dict[str, Any] | None = None,
    form_data: dict[str, Any] | None = None,
    *,
    daemon: bool = False,
    flask_app: Flask | None = None,
) -> int:
    job_data: JobData | None = load_job_data(job_type)
    job_class = job_data.job_class if job_data else None

    if not job_data or not job_class:
        raise ValueError(f"Unknown job type: {job_type}")

    username = auth_payload.get("username") if auth_payload else None
    if not username:
        raise ValueError("User authentication data is required")

    resolved_args = _load_job_args(job_data.job_args) if job_data.job_args else {}
    if args:
        resolved_args.update(args)

    # Remove sensitive keys before storing
    resolved_args = _sanitize_args(resolved_args)

    try:
        # Create job record
        job = JobsService().create_job(job_type, username)
    except DuplicateRecordError:
        logger.warning(
            "Attempted to start duplicate job of type '%s' by user '%s'",
            job_type,
            username,
        )
        raise
    except Exception:
        logger.exception("Failed to create job record for job type %s", job_type)
        raise

    # Save payload (no user/token data — identity is rebuilt from job.username)
    payload: dict[str, Any] = {
        "args": resolved_args,
        "form_data": form_data,
        "user": auth_payload or {},
    }

    backend = ThreadBackend()
    backend.start(job, job_data, payload)

    logger.info(
        "Started background job job_type: %r, job created in DB with id: %r",
        job.job_type,
        job.id,
    )

    return job.id


def start_job_form(
    auth_payload: dict[str, Any] | None,
    job_type: str,
    args: dict[str, Any] | None = None,
    form_data: dict[str, Any] | None = None,
) -> int:
    """Start a background job as a daemon thread. Returns the job ID."""
    return _start_job_impl(
        auth_payload,
        job_type,
        args,
        form_data,
        daemon=True,
        flask_app=current_app._get_current_object(),  # type: ignore[attr-defined]
    )


def start_job(
    auth_payload: dict[str, Any] | None,
    job_type: str,
    args: dict[str, Any] | None = None,
) -> int:
    """Start a background job as a daemon thread. Returns the job ID."""
    return _start_job_impl(
        auth_payload,
        job_type,
        args,
        daemon=True,
        flask_app=current_app._get_current_object(),  # type: ignore[attr-defined]
    )


def start_job_cli(
    auth_payload: dict[str, Any] | None,
    job_type: str,
    args: dict[str, Any] | None = None,
    app: Flask | None = None,
) -> int:
    """Start a background job from CLI. Returns the job ID."""
    flask_app = app or current_app._get_current_object()  # type: ignore[attr-defined]
    return _start_job_impl(
        auth_payload,
        job_type,
        args,
        flask_app=flask_app,
    )


__all__ = [
    "start_job_form",
    "start_job",
    "start_job_cli",
    "cancel_job_worker",
]
