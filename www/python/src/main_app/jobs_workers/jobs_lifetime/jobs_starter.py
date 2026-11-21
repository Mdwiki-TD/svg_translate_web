"""Worker module for managing background jobs."""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, current_app

from ...database.services import JobsService, SettingsService
from ..admin_jobs_workers.workers_list import jobs_data_admins
from ..objects import JobData
from ..public_jobs_workers.workers_list_public import jobs_data_public
from .jobs_queue import EnqueueResult, JobsQueue

logger = logging.getLogger(__name__)


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


def load_job_data(job_type: str) -> JobData | None:
    return jobs_data_admins.get(job_type) or jobs_data_public.get(job_type)


def _sanitize_args(args: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive or unnecessary keys from args before storing."""
    cleaned = dict(args)
    cleaned.pop("csrf_token", None)
    return cleaned


class JobStarter:
    """Validates job requests and submits them to the job queue.

    A submission is always accepted: when another job of the same type holds
    the active slot the new job waits in the FIFO queue and is dispatched as
    soon as the slot is free.
    """

    def __init__(
        self,
        jobs_service: JobsService | None = None,
        backend_cls: type | None = None,
        jobs_queue: JobsQueue | None = None,
    ) -> None:
        """Initialize with optional dependencies.

        Args:
            jobs_service: Jobs service instance. Falls back to default if None.
            backend_cls: Backend class used by the queue. Falls back to
                ThreadBackend when None.
            jobs_queue: Queue used to enqueue and dispatch jobs.
        """
        self.jobs_service = jobs_service or JobsService()
        self._backend_cls = backend_cls
        self._jobs_queue = jobs_queue

    @property
    def jobs_queue(self) -> JobsQueue:
        if self._jobs_queue is None:
            backend = self._backend_cls() if self._backend_cls else None
            self._jobs_queue = JobsQueue(jobs_service=self.jobs_service, backend=backend)
        return self._jobs_queue

    def _submit_impl(
        self,
        auth_payload: dict[str, Any] | None,
        job_type: str,
        args: dict[str, Any] | None = None,
        form_data: dict[str, Any] | None = None,
        *,
        daemon: bool = False,
        flask_app: Flask | None = None,
    ) -> EnqueueResult:
        """Validate the request, persist a pending job, and dispatch when possible.

        Args:
            auth_payload: Authenticated user data; only the username is stored.
            job_type: Registered job type.
            args: Caller supplied arguments.
            form_data: Submitted form data.
            daemon: Kept for backward compatibility; the backend decides.
            flask_app: Kept for backward compatibility; unused here.

        Returns:
            The queue outcome (job id, queued flag, queue position).
        """
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

        result = self.jobs_queue.enqueue(
            job_type,
            username,
            args=resolved_args,
            form_data=form_data,
        )

        logger.info(
            "Submitted background job job_type: %r, job id: %r, queued: %r, position: %r",
            job_type,
            result.job_id,
            result.queued,
            result.position,
        )

        return result

    def submit_form(
        self,
        auth_payload: dict[str, Any] | None,
        job_type: str,
        args: dict[str, Any] | None = None,
        form_data: dict[str, Any] | None = None,
    ) -> EnqueueResult:
        """Submit a job with form data; returns the queue outcome."""
        return self._submit_impl(
            auth_payload,
            job_type,
            args,
            form_data,
            daemon=True,
            flask_app=current_app._get_current_object(),  # type: ignore[attr-defined]
        )

    def submit(
        self,
        auth_payload: dict[str, Any] | None,
        job_type: str,
        args: dict[str, Any] | None = None,
    ) -> EnqueueResult:
        """Submit a job; returns the queue outcome."""
        return self._submit_impl(
            auth_payload,
            job_type,
            args,
            daemon=True,
            flask_app=current_app._get_current_object(),  # type: ignore[attr-defined]
        )

    def start_form(
        self,
        auth_payload: dict[str, Any] | None,
        job_type: str,
        args: dict[str, Any] | None = None,
        form_data: dict[str, Any] | None = None,
    ) -> int:
        """Start a background job with form data. Returns the job ID."""
        return self.submit_form(auth_payload, job_type, args, form_data).job_id

    def start(
        self,
        auth_payload: dict[str, Any] | None,
        job_type: str,
        args: dict[str, Any] | None = None,
    ) -> int:
        """Start a background job. Returns the job ID."""
        return self.submit(auth_payload, job_type, args).job_id

    def start_cli(
        self,
        auth_payload: dict[str, Any] | None,
        job_type: str,
        args: dict[str, Any] | None = None,
        app: Flask | None = None,
    ) -> int:
        """Start a background job from CLI. Returns the job ID."""
        flask_app = app or current_app._get_current_object()  # type: ignore[attr-defined]
        return self._submit_impl(
            auth_payload,
            job_type,
            args,
            flask_app=flask_app,
        ).job_id


__all__ = [
    "JobStarter",
    "EnqueueResult",
]
