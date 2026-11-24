# src/main_app/jobs/jobs_lifetime/job_creator.py
"""Job creation: validate, resolve args, create the DB record and store the payload.

Creation never runs or dispatches anything. Running is ``JobExecutor``; dispatching is the backends.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ...database.exceptions import DuplicateRecordError
from ...database.models import JobRecord
from ...database.services import JobsService, SettingsService
from ...jobs_workers.objects import JobData
from ..registry import load_job_data

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


def _sanitize_args(args: dict[str, Any]) -> dict[str, Any]:
    """Remove sensitive or unnecessary keys from args before storing."""
    cleaned = dict(args)
    cleaned.pop("csrf_token", None)
    return cleaned


@dataclass(frozen=True)
class CreatedJob:
    job: JobRecord
    job_data: JobData
    payload: dict[str, Any]


class JobCreator:
    """Creates a job record and persists its payload."""

    def __init__(self, jobs_service: JobsService | None = None) -> None:
        """Initialize with optional dependencies."""
        self.jobs_service = jobs_service or JobsService()

    def create(
        self,
        *,
        username: str,
        job_type: str,
        backend_name: str,
        args: dict[str, Any] | None = None,
        form_data: dict[str, Any] | None = None,
    ) -> CreatedJob:
        """Create the record for ``job_type`` and save its payload.

        The payload never contains user/token data: identity is rebuilt from ``job.username``
        (pods) or passed in memory (threads).

        Raises:
            ValueError: unknown job type or missing username.
            DuplicateRecordError: the same job is already active.
        """
        job_data = load_job_data(job_type)
        if not job_data or not job_data.job_class:
            raise ValueError(f"Unknown job type: {job_type}")

        if not username:
            raise ValueError("User authentication data is required")

        resolved_args = _load_job_args(job_data.job_args) if job_data.job_args else {}
        if args:
            resolved_args.update(args)

        # Remove sensitive keys before storing
        resolved_args = _sanitize_args(resolved_args)

        try:
            # Create job record
            job = self.jobs_service.create_job(job_type, username)
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
        }
        self.jobs_service.save_payload(job.id, backend_name, payload)

        return CreatedJob(job=job, job_data=job_data, payload=payload)


__all__ = [
    "CreatedJob",
    "JobCreator",
]
