"""Worker module for managing background jobs."""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, current_app

from ...database.exceptions import DuplicateRecordError
from ...database.services import JobsService, SettingsService
from ..admin_jobs_workers.workers_list import jobs_data_admins
from ..backends.thread_backend import ThreadBackend
from ..objects import JobData
from ..public_jobs_workers.workers_list_public import jobs_data_public

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


def load_job_data(job_type) -> JobData | None:
    return jobs_data_admins.get(job_type) or jobs_data_public.get(job_type)


def _sanitize_args(args: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive or unnecessary keys from args before storing."""
    cleaned = dict(args)
    cleaned.pop("csrf_token", None)
    return cleaned


class JobStarter:
    """Manages starting background jobs."""

    def __init__(
        self,
        jobs_service: JobsService | None = None,
        backend_cls: type[ThreadBackend] | None = None,
    ) -> None:
        """Initialize with optional dependencies.

        Args:
            jobs_service: Jobs service instance. Falls back to default if None.
            backend_cls: Backend class to use. Falls back to ThreadBackend if None.
        """
        self.jobs_service = jobs_service or JobsService()
        self._backend_cls = backend_cls or ThreadBackend

    def _start_impl(
        self,
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

        jobs_svc = JobsService()

        try:
            # Create job record
            job = jobs_svc.create_job(job_type, username)
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

    def start_form(
        self,
        auth_payload: dict[str, Any] | None,
        job_type: str,
        args: dict[str, Any] | None = None,
        form_data: dict[str, Any] | None = None,
    ) -> int:
        """Start a background job as a daemon thread with form data."""
        return self._start_impl(
            auth_payload,
            job_type,
            args,
            form_data,
            daemon=True,
            flask_app=current_app._get_current_object(),  # type: ignore[attr-defined]
        )

    def start(
        self,
        auth_payload: dict[str, Any] | None,
        job_type: str,
        args: dict[str, Any] | None = None,
    ) -> int:
        """Start a background job as a daemon thread."""
        return self._start_impl(
            auth_payload,
            job_type,
            args,
            daemon=True,
            flask_app=current_app._get_current_object(),  # type: ignore[attr-defined]
        )

    def start_cli(
        self,
        auth_payload: dict[str, Any] | None,
        job_type: str,
        args: dict[str, Any] | None = None,
        app: Flask | None = None,
    ) -> int:
        """Start a background job from CLI. Returns the job ID."""
        flask_app = app or current_app._get_current_object()  # type: ignore[attr-defined]
        return self._start_impl(
            auth_payload,
            job_type,
            args,
            flask_app=flask_app,
        )


__all__ = [
    "JobStarter",
]
