"""Worker module for managing background jobs."""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, current_app

from ..database.models import JobRecord
from ..database.services import JobsService
from ..io.jobs_files_service import JobFilesService
from .backends.thread_backend import ThreadBackend

logger = logging.getLogger(__name__)


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
        self._jobs_service = jobs_service
        self._backend_cls = backend_cls or ThreadBackend

    def _get_jobs_service(self) -> JobsService:
        """Get the jobs service (lazy initialization)."""
        if self._jobs_service is None:
            self._jobs_service = JobsService()
        return self._jobs_service

    def _load_job_args(self, job_args: list[dict[str, str]]) -> dict[str, Any]:
        """Load job arguments from settings."""
        return _load_job_args(job_args)

    def _sanitize_args(self, args: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive or unnecessary keys from args."""
        return _sanitize_args(args)

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
        """Core job start implementation."""
        return _start_job_impl(
            auth_payload,
            job_type,
            args,
            form_data,
            daemon=daemon,
            flask_app=flask_app,
            jobs_service=self._get_jobs_service(),
            backend_cls=self._backend_cls,
        )

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
        """Start a background job from CLI."""
        flask_app = app or current_app._get_current_object()  # type: ignore[attr-defined]
        return self._start_impl(
            auth_payload,
            job_type,
            args,
            flask_app=flask_app,
        )


class JobCanceller:
    """Manages cancelling running jobs."""

    def __init__(
        self,
        jobs_files_service: JobFilesService | None = None,
        jobs_service: JobsService | None = None,
    ) -> None:
        """Initialize with optional dependencies.

        Args:
            jobs_files_service: Job files service. Falls back to default if None.
            jobs_service: Jobs service. Falls back to default if None.
        """
        self._jobs_files_service = jobs_files_service or JobFilesService()
        self._jobs_service = jobs_service

    def _get_jobs_service(self) -> JobsService:
        """Get the jobs service (lazy initialization)."""
        if self._jobs_service is None:
            self._jobs_service = JobsService()
        return self._jobs_service

    def cancel(
        self,
        job_id: int,
        job_type: str | None = None,
        job: JobRecord | None = None,
    ) -> bool:
        """Cancel a running job."""
        return cancel_job_worker(job_id, job_type, job)


__all__ = [
    "JobStarter",
    "JobCanceller",
]
