"""Abstract interface for job execution backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ...database.models import JobRecord
from ..objects import JobData


class JobBackend(ABC):
    """Unified interface for starting, cancelling, and querying jobs.

    Two implementations exist:
    - ``ThreadBackend``: runs jobs in threads inside the Flask process (dev/tests).
    - ``ToolforgeBackend``: runs jobs as Kubernetes pods via Toolforge Jobs API.
    """

    @abstractmethod
    def start(
        self,
        job: JobRecord,
        job_data: JobData,
        user: dict[str, Any] | None = None,
    ) -> str:
        """Start a job and return a backend-specific identifier (e.g. Toolforge name).

        The args/form_data payload is already saved on the job record; the executor reads it from the DB.

        Args:
            job: The database record (already created, payload already saved).
            job_data: The JobData descriptor for this job type.
            user: Auth payload, kept in memory only and never persisted. Used by in-process backends;
                out-of-process backends ignore it and rebuild the identity from ``job.username``.

        Returns:
            A backend-specific identifier (thread id string or Toolforge job name).
        """
        ...

    @abstractmethod
    def cancel(self, job: JobRecord) -> bool:
        """Request cancellation of a running job.

        Returns:
            True if cancellation was successfully requested.
        """
        ...

    def status(self, job: JobRecord) -> dict[str, Any] | None:
        """Query the live status of a job from the backend.

        Returns:
            A dict with keys ``short``, ``duration``, ``messages``, ``detail``
            or None if the job is not found in the backend.
        """
        return None

    def logs(self, job: JobRecord, tail: int = 200) -> str:
        """Retrieve the logs for a job.

        Returns:
            The last ``tail`` lines of the job's output.
        """
        return ""


__all__ = [
    "JobBackend",
]
