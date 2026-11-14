"""Service layer for the Toolforge jobs pages. Flask-free.

The HTTP calls live in ToolforgeJobsService; this module only shapes the
results for the pages and the job actions (show, logs, restart, delete).
Response shapes follow the Toolforge OpenAPI spec (see toolforge_jobs_types.py).
"""

from __future__ import annotations

import logging
import os
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import requests
from dacite import DaciteError

from ...api_services.clients import ToolforgeJobsService
from ...api_services.clients.toolforge.toolforge_jobs_api_service import ToolforgeApiError
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

# Failures a page turns into flash messages instead of raising. DaciteError is raised when
# the API answers with a shape that toolforge_jobs_types does not expect.
_API_ERRORS = (requests.RequestException, ValueError, OSError, DaciteError)

# Toolforge API message levels mapped to flash categories.
_LEVEL_TO_CATEGORY = {
    "info": "info",
    "warning": "warning",
    "error": "danger",
}

# Job name rules from the OpenAPI spec.
JOB_NAME_PATTERN = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?([.][a-z0-9]([-a-z0-9]*[a-z0-9])?)*$")
JOB_NAME_MAX_LENGTH = 52


LOG_FILE_STREAMS = ("stdout", "stderr")
ALLOWED_LOG_SUFFIXES = {".out", ".err", ".log"}
MAX_LOG_BYTES = 1_000_000  # only the end of a log file is read


class JobsPageServiceHelpers:
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

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
        self.toolforge = toolforge or ToolforgeJobsService()

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
        """Log an API failure and return the flash messages for it."""
        messages: list[Message] = []

        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            if isinstance(exc, ToolforgeApiError):
                # The client already parsed the bare error body (ResponseMessages).
                messages = self._convert_messages(self._extract_messages(exc.messages))
            else:
                messages = self._convert_messages(self._extract_messages(self._body_of(exc.response)))

            msg = self._message_by_code(action, exc.response.status_code)
            if msg[0]:  # ("", "") means no specific text for this status code
                messages.insert(0, msg)
                return messages

        # No traceback here: the exception text can contain the token URL.
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
            except _API_ERRORS as exc:
                return JobsPage(
                    messages=self._failure_messages(action, exc),
                    error=True,
                )

        jobs = payload.jobs or []
        summary = Counter(j.status_key for j in jobs)

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
            job = payload.job

        except _API_ERRORS as exc:
            return JobDetailPage(
                job_id=job_id,
                messages=self._failure_messages(action, exc),
                error=True,
            )

        return JobDetailPage(
            job_id=job_id,
            job=job,
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
        except _API_ERRORS as exc:
            return JobLogsPage(
                job_id=job_id,
                lines=lines,
                messages=self._failure_messages(action, exc),
                error=True,
            )

        return JobLogsPage.read(job_id, text, lines)

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
        except Exception as exc:
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

    @staticmethod
    def _body_of(response: requests.Response) -> Any:
        """Return the JSON body of a response, or {} when it has none."""
        try:
            return response.json()
        except Exception:
            return {}

    @staticmethod
    def _extract_messages(payload: Any) -> dict[str, list[str]]:
        """Return the non-empty ``info``/``warning``/``error`` lists of an API result.

        ``payload`` is a ResponseMessages, a response dataclass (``payload.messages``)
        or, for legacy callers, a raw dict (``{"messages": {...}}`` or a bare body).
        """
        raw: Any = {}
        if is_dataclass(payload) and not isinstance(payload, type):
            inner = getattr(payload, "messages", payload)  # ResponseMessages has no `messages`
            raw = asdict(inner) if is_dataclass(inner) and not isinstance(inner, type) else {}

        elif isinstance(payload, dict):
            raw = payload.get("messages") or {}
            if not isinstance(raw, dict) or not raw:
                raw = {level: payload[level] for level in _LEVEL_TO_CATEGORY.keys() if payload.get(level)}

        return {level: texts for level, texts in raw.items() if texts}

    def read_job_log_file(self, job_id: str, filelog: str, lines: int = DEFAULT_LOG_LINES) -> JobLogsPage:
        """Read the end of the stdout/stderr file of a job, never raising."""
        lines = min(max(lines, 1), MAX_LOG_LINES)

        if filelog not in LOG_FILE_STREAMS:
            return JobLogsPage(
                job_id=job_id,
                lines=lines,
                error=True,
                messages=[(f"Unknown log file: {filelog[:20]!r}", "danger")],
            )
        invalid = self._invalid_name_message(job_id)
        if invalid:
            return JobLogsPage(job_id=job_id, lines=lines, messages=[invalid], error=True)

        action = f"read the {filelog} file of job '{job_id}'"
        try:
            job = self.toolforge.show_job(job_id).job
            file_name = None
            if job:
                file_name = job.filelog_stdout if filelog == "stdout" else job.filelog_stderr

            if not file_name:
                return JobLogsPage(
                    job_id=job_id,
                    lines=lines,
                    filelog=filelog,
                    messages=[(f"Job '{job_id}' has no {filelog} file (filelog is disabled).", "warning")],
                )
            text = self.read_file(self._log_file_path(file_name))
        except _API_ERRORS as exc:  # includes OSError (missing file, permissions) and PermissionError below
            return JobLogsPage(
                job_id=job_id,
                lines=lines,
                filelog=filelog,
                error=True,
                messages=self._failure_messages(action, exc),
            )

        return JobLogsPage.read(job_id, text, lines, filelog)

    def _log_file_path(self, file_name: str) -> Path:
        """Resolve a log path from the job definition; it must stay a log file inside the tool home.

        The path comes from the job definition (anyone who can create jobs controls it),
        so it is never trusted: otherwise ``/etc/passwd`` or ``~/.toolskube/client.key`` could be shown.
        """
        home = Path(self.toolforge.api.home_dir).resolve()
        path = Path(file_name)
        if not path.is_absolute():
            path = home / path  # "logs/my-job.out" is relative to the tool home
        path = path.resolve()  # follows symlinks and removes ".."

        if not path.is_relative_to(home):
            raise PermissionError("the log file is outside the tool directory")
        if path.suffix not in ALLOWED_LOG_SUFFIXES:
            raise PermissionError(f"only {', '.join(sorted(ALLOWED_LOG_SUFFIXES))} files can be read")
        if any(part.startswith(".") for part in path.relative_to(home).parts):
            raise PermissionError("hidden files and directories cannot be read")
        return path

    @staticmethod
    def read_file(path: Path, max_bytes: int = MAX_LOG_BYTES) -> str:
        """Return the end of a file (at most ``max_bytes``), without loading it all."""
        if not path.is_file():
            raise FileNotFoundError(f"{path.name} does not exist")

        with path.open("rb") as handle:
            size = handle.seek(0, os.SEEK_END)
            handle.seek(max(size - max_bytes, 0))
            data = handle.read()

        text = data.decode("utf-8", errors="replace")
        if size > max_bytes:
            text = text.split("\n", 1)[-1]  # drop the partial first line

        return text


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
