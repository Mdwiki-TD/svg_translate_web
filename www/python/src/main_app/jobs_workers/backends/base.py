"""Abstract base class for job backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ...database.models import JobRecord
from ..objects import JobData


class JobBackend(ABC):
    """Abstract interface for job execution backends."""

    @abstractmethod
    def start(
        self,
        job: JobRecord,
        job_data: JobData,
        payload: dict[str, Any],
    ) -> str:
        """Start a job and return a backend-specific handle."""

    @abstractmethod
    def cancel(self, job: JobRecord) -> bool:
        """Request cancellation of a running job. Returns True if handled."""


__all__ = [
    "JobBackend",
]
