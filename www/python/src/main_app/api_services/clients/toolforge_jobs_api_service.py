"""Standalone client for the Toolforge Jobs API. Flask-free.

Every method maps to one endpoint of ``/jobs/v1`` and returns what the
OpenAPI spec says it returns (see toolforge_jobs_types.py): a dict for the
JSON endpoints and a plain string for the logs. A non-JSON body on a JSON
endpoint raises ``ValueError``. Use ``request()`` directly to get the raw
``requests.Response`` (status code, headers, body).
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

from .http_client import HttpClient
from .toolforge_api_service import ToolforgeApiService
from .toolforge_jobs_types import (
    ImagesResponse,
    JobListResponse,
    JobResponse,
    MessagesResponse,
    NewJob,
    QuotaResponse,
    UpdateResponse,
)

logger = logging.getLogger(__name__)


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
        check: bool | None = None,
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
        self.check = check if check is not None else True

    @staticmethod
    def _job_path(job_id: str | int) -> str:
        """Return the sub-path of a single job (``job_id`` is the job name)."""
        return f"/jobs/{quote(str(job_id), safe='')}"

    def _json(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        """
        Send a request to a JSON endpoint and return the decoded body
        """
        json_response = self.api.request(
            method,
            path,
            params=params,
            json=json,
            check=self.check,
        )

        # Response (400) might return {'error': ['Unable to restart a one-off job']}
        try:
            return json_response.json()
        except Exception:
            logger.warning(
                "JSON response not decoded: %s",
                json_response.text,
            )

            # raise the HTTPError if it's not a 200
            if json_response.status_code != 200:
                json_response.raise_for_status()

            # raise the `json_response.json()` error if it's not JSON
            raise

    # ------------------------------------------------------------------
    # Endpoints (healthcheck() and metrics() are inherited)
    # ------------------------------------------------------------------

    def images(self) -> ImagesResponse:
        """GET /jobs/v1/tool/{tool}/images: ``{"images": [{shortname, image}], "messages"}``."""
        return self._json(
            "GET",
            self.api._tool_path("/images"),
        )

    def quotas(self) -> QuotaResponse:
        """GET /jobs/v1/tool/{tool}/quotas: ``{"quota": {"categories": [...]}, "messages"}``."""
        return self._json(
            "GET",
            self.api._tool_path("/quotas"),
        )

    def list_jobs(self, include_unset: bool | None = None) -> JobListResponse:
        """GET /jobs/v1/tool/{tool}/jobs: ``{"jobs": [Job, ...], "messages"}``.

        ``include_unset``: when unset or True the API includes all the fields,
        also those that were not passed on job creation.
        """
        return self._json(
            "GET",
            self.api._tool_path("/jobs"),
            params={"include_unset": include_unset},
        )

    def create_job(self, data: NewJob) -> JobResponse:
        """POST /jobs/v1/tool/{tool}/jobs: create a job, returns ``{"job": Job, "messages"}``."""
        return self._json(
            "POST",
            self.api._tool_path("/jobs"),
            json=data,
        )

    def update_job(self, data: NewJob) -> UpdateResponse:
        """PATCH /jobs/v1/tool/{tool}/jobs: update or create a job, ``{"messages", "job_changed"}``."""
        return self._json(
            "PATCH",
            self.api._tool_path("/jobs"),
            json=data,
        )

    def flush_jobs(self) -> MessagesResponse:
        """DELETE /jobs/v1/tool/{tool}/jobs: delete ALL jobs of the tool, ``{"messages"}``."""
        return self._json(
            "DELETE",
            self.api._tool_path("/jobs"),
        )

    # ------------------------------------------------------------------
    # Per jobs endpoints
    # ------------------------------------------------------------------

    def show_job(self, job_id: str | int) -> JobResponse:
        """GET /jobs/v1/tool/{tool}/jobs/{id}: ``{"job": Job, "messages"}``. 404 if it does not exist."""
        return self._json(
            "GET",
            self.api._tool_path(self._job_path(job_id)),
        )

    def delete_job(self, job_id: str | int) -> MessagesResponse:
        """DELETE /jobs/v1/tool/{tool}/jobs/{id}: ``{"messages"}``. 404 if it does not exist."""
        return self._json(
            "DELETE",
            self.api._tool_path(self._job_path(job_id)),
        )

    def get_logs(self, job_id: str | int) -> str:
        """GET /jobs/v1/tool/{tool}/jobs/{id}/logs: the logs as plain text (``text/plain``).

        The endpoint takes no query parameters, so the lines cannot be limited here.
        """
        response_data = self.api.request(
            "GET",
            self.api._tool_path(f"{self._job_path(job_id)}/logs"),
        )
        return response_data.text

    def restart_job(
        self,
        job_id: str | int,
    ) -> MessagesResponse:
        """POST /jobs/v1/tool/{tool}/jobs/{id}/restart: ``{"messages"}`` (a cronjob runs right now)."""
        return self._json(
            "POST",
            self.api._tool_path(f"{self._job_path(job_id)}/restart"),
        )

    def list_jobs_test(self, include_unset: bool | None = None) -> JobListResponse:
        data = {
            "jobs": [
                {
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
                    "filelog_stdout": "/data/project/mdw/update.out",
                    "filelog_stderr": "/data/project/mdw/update.err",
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
            ],
            "messages": {"info": [], "warning": [], "error": []},
        }
        return JobListResponse(
            jobs=data["jobs"],
            messages=data["messages"],
        )

    def healthcheck(self) -> Any:
        return self.api.healthcheck()

    def metrics(self) -> Any:
        return self.api.metrics()

    def redact(self, text: str) -> Any:
        return self.api.redact(text)


__all__ = [
    "ToolforgeJobsService",
]
