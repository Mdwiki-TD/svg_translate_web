"""Service layer for the Toolforge jobs pages. Flask-free.

The HTTP calls live in ToolforgeJobsService; this module only shapes the
results for the pages and the job actions (show, logs, restart, delete).
Response shapes follow the Toolforge OpenAPI spec (see toolforge_jobs_types.py).
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from collections.abc import Callable
from typing import Any

import requests

from ...api_services.clients import ToolforgeJobsService
from .toolforge_jobs_mapping import (
    DEFAULT_LOG_LINES,
    MAX_LOG_LINES,
    JobActionResult,
    JobDetailPage,
    JobLogsPage,
    JobsPage,
    Message,
)

logger = logging.getLogger(__name__)

# Toolforge API message levels mapped to flash categories.
_LEVEL_TO_CATEGORY = {
    "info": "info",
    "warning": "warning",
    "error": "danger",
}

# Job name rules from the OpenAPI spec.
JOB_NAME_PATTERN = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?([.][a-z0-9]([-a-z0-9]*[a-z0-9])?)*$")
JOB_NAME_MAX_LENGTH = 52


class JobsPageServiceHelpers:
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _job_status(job: dict[str, Any]) -> str:
        """Return a lowercase short status: pending, running, succeeded, failed or unknown."""
        status = job.get("status") or {}
        short = status.get("short") or job.get("status_short") or "unknown"
        # The legacy status_short is free text such as "Running."
        return str(short).lower().rstrip(".")

    @classmethod
    def _normalize_job(cls, job: dict | dict[str, Any]) -> dict[str, Any]:
        """Add the keys the templates use (status_key, status_messages, health_check_text)."""
        job = job or {}
        job["status_key"] = cls._job_status(job)
        job["status_messages"] = (job.get("status") or {}).get("messages", [])

        health_check = job.get("health_check")
        if isinstance(health_check, dict):
            target = health_check.get("script") or health_check.get("path") or ""
            job["health_check_text"] = f"{health_check.get('type', '')}: {target}".strip(": ")
        else:
            job["health_check_text"] = None

        return job

    @staticmethod
    def _convert_messages(raw: Any) -> list[Message]:
        """Convert the API ``messages`` object (info/warning/error lists) to (text, category) pairs."""
        if not isinstance(raw, dict):
            return []
        messages: list[Message] = []
        for level, texts in raw.items():
            category = _LEVEL_TO_CATEGORY.get(level, "info")
            messages.extend((str(text), category) for text in texts or [])
        return messages

    @staticmethod
    def _invalid_name_message(job_id: str) -> Message | None:
        """Return an error message when ``job_id`` cannot be a job name, else None."""
        if len(job_id) <= JOB_NAME_MAX_LENGTH and JOB_NAME_PATTERN.match(job_id):
            return None
        return (f"Invalid job name: {job_id[:60]!r}", "danger")


class JobsPageService(JobsPageServiceHelpers):
    """Build the data of the jobs pages from the Toolforge Jobs API."""

    def __init__(self, toolforge: ToolforgeJobsService | None = None) -> None:
        self.toolforge = toolforge or ToolforgeJobsService(check=True)

    def _message_by_code(self, action: str, code: int) -> Message:
        if code == 400:
            logger.warning("Failed to %s: bad request", action)
            return (f"Failed to {action}: bad request (400).", "danger")

        if code == 404:
            logger.warning("Failed to %s: not found", action)
            return (f"Failed to {action}: not found (404).", "danger")

        if code == 401:
            logger.warning("Failed to %s: unauthorized", action)
            return (
                f"Failed to {action}: unauthorized (401), check the client certificate or deploy token.",
                "danger",
            )
        return ("", "")

    def _failure_messages(self, action: str, exc: Exception) -> list[Message]:
        """Log an API failure and return the flash message for it."""
        messages: list[Message] = []

        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            try:
                payload = exc.response.json()
            except Exception:
                payload = {}

            messages = self._convert_messages(self._extract_messages(payload))
            code = exc.response.status_code
            msg = self._message_by_code(action, code)
            if msg:
                messages.insert(0, msg)
                return messages

        if isinstance(exc, (requests.RequestException, ValueError)):
            # No traceback here: the exception text can contain the token URL.
            reason = self.toolforge.api.redact(str(exc))
            logger.error("Failed to %s: %s", action, reason)
            messages.insert(0, (f"Failed to {action}: {reason}", "danger"))
            return messages

        reason = self.toolforge.api.redact(str(exc))
        logger.error("Failed to %s: %s", action, reason)
        messages.insert(0, (f"Failed to {action}: {reason}", "danger"))
        return messages

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    def build_jobs_page(self, test_page: bool = False) -> JobsPage:
        """Fetch the jobs and build the page data, never raising."""
        action = "load Toolforge jobs"
        if test_page:
            payload = self.toolforge.list_jobs_test()
        else:
            try:
                payload = self.toolforge.list_jobs()
            except (requests.RequestException, ValueError, OSError) as exc:
                return JobsPage(
                    messages=self._failure_messages(action, exc),
                    error=True,
                )

        jobs = [self._normalize_job(dict(job)) for job in payload.get("jobs") or []]
        summary = Counter(j["status_key"] for j in jobs)

        return JobsPage(
            jobs=jobs,
            status_summary=dict(summary),
            messages=self._convert_messages(self._extract_messages(payload)),
        )

    def build_job_page(self, job_id: str) -> JobDetailPage:
        """Fetch one job and build the page data, never raising."""
        invalid = self._invalid_name_message(job_id)
        if invalid:
            return JobDetailPage(job_id=job_id, messages=[invalid], error=True)

        action = f"load job '{job_id}'"
        try:
            payload = self.toolforge.show_job(job_id)
            job = payload.get("job")

            if not isinstance(job, dict):
                raise ValueError("Unexpected response from the Toolforge API")

        except (requests.RequestException, ValueError, OSError) as exc:
            return JobDetailPage(
                job_id=job_id,
                messages=self._failure_messages(action, exc),
                error=True,
            )

        return JobDetailPage(
            job_id=job_id,
            job=self._normalize_job(dict(job)),
            messages=self._convert_messages(self._extract_messages(payload)),
        )

    def build_logs_page(self, job_id: str, lines: int = DEFAULT_LOG_LINES) -> JobLogsPage:
        """Fetch the logs (plain text) of one job and keep the last ``lines`` lines, never raising."""
        lines = min(max(lines, 1), MAX_LOG_LINES)
        invalid = self._invalid_name_message(job_id)
        if invalid:
            return JobLogsPage(job_id=job_id, lines=lines, messages=[invalid], error=True)

        action = f"load logs of job '{job_id}'"
        try:
            text = self.toolforge.get_logs(job_id)
        except (requests.RequestException, ValueError, OSError) as exc:
            return JobLogsPage(
                job_id=job_id,
                lines=lines,
                messages=self._failure_messages(action, exc),
                error=True,
            )

        all_lines = text.splitlines()
        return JobLogsPage(
            job_id=job_id,
            logs=all_lines[-lines:],
            lines=lines,
            total_lines=len(all_lines),
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _run_action(
        self,
        action: str,
        call: Callable[[], Any],
        success_text: str,
    ) -> JobActionResult:
        """Run a mutating API call and turn the outcome into flash messages."""
        try:
            payload = call()
        except (requests.RequestException, ValueError, OSError, Exception) as exc:
            return JobActionResult(
                messages=self._failure_messages(action, exc),
                ok=False,
            )

        # Check if the API returned a structured error body despite a 200/400 JSON response
        messages_data = self._extract_messages(payload)
        messages_ready = self._convert_messages(messages_data)

        messages: list[Message] = []
        success = not messages_data.get("error")
        if success:
            messages.append((success_text, "success"))

        messages.extend(messages_ready)

        return JobActionResult(messages=messages, ok=success)

    def restart_job(self, job_id: str) -> JobActionResult:
        """Restart one job (a cronjob runs right now)."""
        invalid = self._invalid_name_message(job_id)
        if invalid:
            return JobActionResult(messages=[invalid], ok=False)

        # self.toolforge.restart_job(job_id)

        return self._run_action(
            action=f"restart job '{job_id}'",
            call=lambda: self.toolforge.restart_job(job_id),
            success_text=f"Job '{job_id}' restarted.",
        )

    def delete_job(self, job_id: str) -> JobActionResult:
        """Delete one job."""
        invalid = self._invalid_name_message(job_id)
        if invalid:
            return JobActionResult(messages=[invalid], ok=False)

        return self._run_action(
            action=f"delete job '{job_id}'",
            call=lambda: self.toolforge.delete_job(job_id),
            success_text=f"Job '{job_id}' deleted.",
        )

    def _extract_messages(self, payload):
        if not isinstance(payload, dict):
            return {}

        messages_data = payload.get("messages") or {}

        if not messages_data:
            if payload.get("info", []):
                messages_data["info"] = payload.get("info", [])

            if payload.get("warning", []):
                messages_data["warning"] = payload.get("warning", [])

            if payload.get("error", []):
                messages_data["error"] = payload.get("error", [])

        return messages_data


__all__ = [
    "DEFAULT_LOG_LINES",
    "JOB_NAME_MAX_LENGTH",
    "JOB_NAME_PATTERN",
    "MAX_LOG_LINES",
    "JobActionResult",
    "JobDetailPage",
    "JobLogsPage",
    "JobsPage",
    "JobsPageService",
    "Message",
]
