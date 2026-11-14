"""Standalone client for the Toolforge Jobs API. Flask-free.

Every method maps to one endpoint of ``/jobs/v1`` and returns what the
OpenAPI spec says it returns (see toolforge_jobs_types.py): a dataclass for the
JSON endpoints and a plain string for the logs.

The shape of the body depends on the HTTP status code:
- below 400: the success body, e.g. ``{"messages": {...}}`` (MessagesResponse);
- 400, 401, 404 ...: a bare ``{"info": [...], "error": [...]}`` (ResponseMessages),
  raised as ``ToolforgeApiError``, an ``requests.HTTPError`` that carries it.

A non-JSON success body on a JSON endpoint raises ``ValueError``. Use
``api.request()`` directly to get the raw ``requests.Response``.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

import requests
from dacite import DaciteError

from ..http_client import HttpClient
from .toolforge_api_service import ToolforgeApiService
from .toolforge_jobs_types import (
    ImagesResponse,
    JobListResponse,
    JobResponse,
    MessagesResponse,
    QuotaResponse,
    ResponseMessages,
    UpdateResponse,
)

logger = logging.getLogger(__name__)


class ToolforgeApiError(requests.HTTPError):
    """The API answered with an error status (>= 400).

    It is a ``requests.HTTPError`` (so ``except requests.HTTPError`` keeps working and
    ``.response`` is set) that also carries the parsed body as ``messages``.
    """

    def __init__(self, response: requests.Response, messages: ResponseMessages) -> None:
        self.messages = messages
        self.status_code = response.status_code
        details = "; ".join(messages.error or [])
        text = f"{response.status_code} error from the Toolforge API"
        super().__init__(f"{text}: {details}" if details else text, response=response)


class ToolforgeJobsService:
    """Thin client for the Toolforge Jobs API."""

    def __init__(
        self,
        tool_name: str | None = None,
        home_dir: str | None = None,
        verify: bool | None = None,
        timeout: int | None = None,
        http_client: HttpClient | None = None,
        token: str | None = None,
        internal: bool | None = None,
    ) -> None:
        self.api = ToolforgeApiService(
            api_route="jobs",
            tool_name=tool_name,
            home_dir=home_dir,
            verify=verify,
            timeout=timeout,
            http_client=http_client,
            token=token,
            internal=internal,
        )

    @staticmethod
    def _job_path(job_id: str | int) -> str:
        """Return the sub-path of a single job (``job_id`` is the job name)."""
        return f"/jobs/{quote(str(job_id), safe='')}"

    @staticmethod
    def _error_from(response: requests.Response) -> ToolforgeApiError:
        """Build the error of a response with an error status (the body is a bare ResponseMessages)."""
        try:
            body = response.json()
        except ValueError:
            body = None

        messages = ResponseMessages()
        if isinstance(body, dict):
            try:
                messages = ResponseMessages.load(body)
            except DaciteError:
                logger.warning("Unexpected error body: %s", response.text)
        else:
            logger.warning("Error body is not a JSON object: %s", response.text)

        return ToolforgeApiError(response, messages)

    def _send(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> requests.Response:
        """Send a request; the status code decides: >= 400 raises ToolforgeApiError."""
        response = self.api.request(method, path, params=params, json=json, check=False)
        if response.status_code >= 400:
            raise self._error_from(response)
        return response

    def _json(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        """Send a request to a JSON endpoint and return the decoded success body.

        Raises ToolforgeApiError on an error status and ValueError when a
        success body is not JSON.
        """
        response = self._send(
            method,
            path,
            params=params,
            json=json,
        )
        try:
            return response.json()
        except ValueError:
            logger.warning("JSON response not decoded: %s", response.text)
            raise

    # ------------------------------------------------------------------
    # Endpoints (healthcheck() and metrics() are inherited)
    # ------------------------------------------------------------------

    def images(self) -> ImagesResponse:
        """GET /jobs/v1/tool/{tool}/images: ``{"images": [{shortname, image}], "messages"}``."""
        data = self._json(
            "GET",
            self.api._tool_path("/images"),
        )
        return ImagesResponse.load(data)

    def quotas(self) -> QuotaResponse:
        """GET /jobs/v1/tool/{tool}/quotas: ``{"quota": {"categories": [...]}, "messages"}``."""
        data = self._json(
            "GET",
            self.api._tool_path("/quotas"),
        )
        return QuotaResponse.load(data)

    def list_jobs(self, include_unset: bool | None = None) -> JobListResponse:
        """GET /jobs/v1/tool/{tool}/jobs: ``{"jobs": [Job, ...], "messages"}``.

        ``include_unset``: when unset or True the API includes all the fields,
        also those that were not passed on job creation.
        """
        data = self._json(
            "GET",
            self.api._tool_path("/jobs"),
            params={"include_unset": include_unset},
        )
        return JobListResponse.load(data)

    def create_job(self, data: dict[str, Any]) -> JobResponse:
        """POST /jobs/v1/tool/{tool}/jobs: create a job, returns ``{"job": Job, "messages"}``."""
        result = self._json(
            "POST",
            self.api._tool_path("/jobs"),
            json=data,
        )
        return JobResponse.load(result)

    def update_job(self, data: dict[str, Any]) -> UpdateResponse:
        """PATCH /jobs/v1/tool/{tool}/jobs: update or create a job, ``{"messages", "job_changed"}``."""
        result = self._json(
            "PATCH",
            self.api._tool_path("/jobs"),
            json=data,
        )
        return UpdateResponse.load(result)

    def flush_jobs(self) -> MessagesResponse:
        """DELETE /jobs/v1/tool/{tool}/jobs: delete ALL jobs of the tool, ``{"messages"}``."""
        data = self._json(
            "DELETE",
            self.api._tool_path("/jobs"),
        )
        return MessagesResponse.load(data)

    # ------------------------------------------------------------------
    # Per jobs endpoints
    # ------------------------------------------------------------------

    def show_job(self, job_id: str | int) -> JobResponse:
        """GET /jobs/v1/tool/{tool}/jobs/{id}: ``{"job": Job, "messages"}``. 404 if it does not exist."""
        data = self._json(
            "GET",
            self.api._tool_path(self._job_path(job_id)),
        )
        return JobResponse.load(data)

    def delete_job(self, job_id: str | int) -> MessagesResponse:
        """DELETE /jobs/v1/tool/{tool}/jobs/{id}: ``{"messages"}``. 404 if it does not exist."""
        data = self._json(
            "DELETE",
            self.api._tool_path(self._job_path(job_id)),
        )
        return MessagesResponse.load(data)

    def get_logs(self, job_id: str | int) -> str:
        """GET /jobs/v1/tool/{tool}/jobs/{id}/logs: the logs as plain text (``text/plain``).

        The endpoint takes no query parameters, so the lines cannot be limited here.
        """
        response = self._send(
            "GET",
            self.api._tool_path(f"{self._job_path(job_id)}/logs"),
        )
        return response.text

    def restart_job(
        self,
        job_id: str | int,
    ) -> MessagesResponse:
        """POST /jobs/v1/tool/{tool}/jobs/{id}/restart: ``{"messages"}`` (a cronjob runs right now)."""
        data = self._json(
            "POST",
            self.api._tool_path(f"{self._job_path(job_id)}/restart"),
        )
        return MessagesResponse.load(data)

    def list_jobs_test(self, include_unset: bool | None = None) -> JobListResponse:
        simple_job = self.simple_job()

        return JobListResponse.load(
            {
                "jobs": [simple_job],
                "messages": {"info": [], "warning": [], "error": []},
            }
        )

    def simple_job(self):
        return {
            "name": "update",
            "imagename": "python3.13",
            "mount": "all",
            "memory": "0.5Gi",
            "cpu": "0.1",
            "emails": "none",
            "image": "python3.13",
            "image_state": "stable",
            "status_short": "Failed",
            "status_long": 'Last run at 2026-11-03T22: 46: 26Z. Pod in "Failed" phase. State "terminated". Reason "Error". Started at "2026-11-03T22: 46: 30Z". Finished at "2026-11-03T22: 46: 30Z". Exit code "127".',
            "filelog": True,
            "filelog_stdout": "/data/project/z/update.out",
            "filelog_stderr": "/data/project/z/update.err",
            "cmd": "~/shs/update.shz",
            "job_type": "one-off",
            "retry": 0,
            "status": {
                "short": "failed",
                "duration": "3s",
                "up_to_date": True,
                "messages": ["exitcode 127"],
            },
        }

    def healthcheck(self) -> Any:
        return self.api.healthcheck()

    def metrics(self) -> Any:
        return self.api.metrics()

    def redact(self, text: str) -> Any:
        return self.api.redact(text)


__all__ = [
    "ToolforgeApiError",
    "ToolforgeJobsService",
]
