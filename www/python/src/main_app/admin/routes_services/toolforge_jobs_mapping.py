""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# (text, category) pair, ready to be passed to flask.flash by the view.
Message = tuple[str, str]

DEFAULT_LOG_LINES = 200
MAX_LOG_LINES = 2000


@dataclass
class JobsPage:
    """Everything the jobs table template needs, plus messages to flash."""

    jobs: list[dict[str, Any]] = field(default_factory=list)
    status_summary: dict[str, int] = field(default_factory=dict)
    messages: list[Message] = field(default_factory=list)
    error: bool = False

    def to_context(self) -> dict[str, Any]:
        """Return the template context."""
        return {
            "jobs": self.jobs,
            "status_summary": self.status_summary,
            "total_jobs": len(self.jobs),
            "error": self.error,
        }


@dataclass
class JobDetailPage:
    """Everything the single job template needs, plus messages to flash."""

    job_id: str
    job: dict[str, Any] | None = None
    messages: list[Message] = field(default_factory=list)
    error: bool = False

    def to_context(self) -> dict[str, Any]:
        """Return the template context."""
        return {"job_id": self.job_id, "job": self.job, "error": self.error}


@dataclass
class JobLogsPage:
    """Everything the job logs template needs, plus messages to flash."""

    job_id: str
    logs: list[str] = field(default_factory=list)
    lines: int = DEFAULT_LOG_LINES
    total_lines: int = 0
    messages: list[Message] = field(default_factory=list)
    error: bool = False

    def to_context(self) -> dict[str, Any]:
        """Return the template context."""
        return {
            "job_id": self.job_id,
            "logs": self.logs,
            "lines": self.lines,
            "total_lines": self.total_lines,
            "max_lines": MAX_LOG_LINES,
            "error": self.error,
        }


@dataclass
class JobActionResult:
    """Outcome of a job action (restart, delete)."""

    messages: list[Message] = field(default_factory=list)
    ok: bool = True
    redirect_endpoint: str = "jobs"


__all__ = [
    "DEFAULT_LOG_LINES",
    "MAX_LOG_LINES",
    "JobActionResult",
    "JobDetailPage",
    "JobLogsPage",
    "JobsPage",
]
