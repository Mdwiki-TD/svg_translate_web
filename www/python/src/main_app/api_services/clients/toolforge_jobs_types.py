"""Response and request shapes of the Toolforge Jobs API.

Taken from the OpenAPI spec (Toolforge API 8.37.3). They are TypedDicts, so
they only document and type-check the data; at runtime everything is a plain
dict. Endpoints that are not JSON return ``str`` instead:
- GET .../jobs/{id}/logs  -> text/plain
- GET /jobs/v1/metrics    -> text/plain
"""

from __future__ import annotations

from typing import Literal, TypedDict

JobType = Literal["one-off", "scheduled", "continuous", "webservice"]
JobStatusShort = Literal["pending", "running", "succeeded", "failed", "unknown"]
EmailOption = Literal["none", "all", "onfinish", "onfailure"]
MountOption = Literal["all", "none"]


class ResponseMessages(TypedDict, total=False):
    """Messages by priority, present in almost every response."""

    info: list[str]
    warning: list[str]
    error: list[str]


class JobStatus(TypedDict, total=False):
    """``job["status"]``: standardized status (``short`` and ``duration`` are always present)."""

    short: JobStatusShort
    duration: str  # e.g. "24d24h59m45s"
    messages: list[str]  # e.g. ["exitcode 127"]
    up_to_date: bool
    previous_schedule: str  # scheduled jobs only, ISO 8601
    next_schedule: str  # scheduled jobs only, ISO 8601


class HealthCheck(TypedDict, total=False):
    """``job["health_check"]``: ``script`` for type "script", ``path`` for type "http"."""

    type: Literal["script", "http"]
    script: str
    path: str


class Job(TypedDict, total=False):
    """A defined job. The fields present depend on ``job_type`` (the spec uses oneOf).

    - all types: name, imagename, image, image_state, memory, cpu, emails, mount,
      status_short, status_long, status, job_type
    - one-off, scheduled, continuous: cmd, filelog, filelog_stdout, filelog_stderr
    - one-off, scheduled: retry
    - scheduled: schedule, schedule_actual, timeout
    - continuous, webservice: replicas, port, health_check
    - continuous: continuous (deprecated), port_protocol, publish
    - webservice: cmd may be empty
    """

    name: str  # 1-52 chars, lowercase, digits, "-" and "."
    imagename: str
    image: str
    image_state: str  # e.g. "stable"
    memory: str | None
    cpu: str | None
    emails: EmailOption
    mount: MountOption
    job_type: JobType
    cmd: str
    retry: int  # 0-5
    schedule: str
    schedule_actual: str
    timeout: int | None
    replicas: int | None
    port: int | None
    port_protocol: Literal["tcp", "udp"]
    publish: str
    continuous: bool
    health_check: HealthCheck | None
    filelog: bool
    filelog_stdout: str | None
    filelog_stderr: str | None
    status_short: str  # legacy text such as "Running."
    status_long: str  # legacy extended text
    status: JobStatus


class NewJob(TypedDict, total=False):
    """Request body of create_job / update_job (a Job without the status fields).

    Required: ``name`` and ``imagename`` (``name`` defaults to "webservice" for
    webservice jobs), plus ``cmd`` for one-off/scheduled/continuous jobs,
    ``schedule`` for scheduled jobs and ``job_type`` for webservice jobs.
    """

    name: str
    imagename: str
    cmd: str
    job_type: JobType
    memory: str | None
    cpu: str | None
    emails: EmailOption
    mount: MountOption
    retry: int
    schedule: str
    timeout: int | None
    replicas: int | None
    port: int | None
    port_protocol: Literal["tcp", "udp"]
    publish: str
    continuous: bool
    health_check: HealthCheck | None
    filelog: bool
    filelog_stdout: str | None
    filelog_stderr: str | None


class JobListResponse(TypedDict, total=False):
    """GET /jobs."""

    jobs: list[Job]
    messages: ResponseMessages


class JobResponse(TypedDict, total=False):
    """GET /jobs/{id} and POST /jobs."""

    job: Job
    messages: ResponseMessages


class MessagesResponse(TypedDict, total=False):
    """DELETE /jobs, DELETE /jobs/{id} and POST /jobs/{id}/restart."""

    messages: ResponseMessages


class UpdateResponse(TypedDict, total=False):
    """PATCH /jobs."""

    messages: ResponseMessages
    job_changed: bool


class Image(TypedDict, total=False):
    """One entry of the images list."""

    shortname: str
    image: str


class ImagesResponse(TypedDict, total=False):
    """GET /images."""

    images: list[Image]
    messages: ResponseMessages


class QuotaItem(TypedDict, total=False):
    """One quota line; ``limit`` and ``used`` are strings (e.g. "1G")."""

    name: str
    limit: str
    used: str


class QuotaCategory(TypedDict, total=False):
    """A group of quota lines."""

    name: str
    items: list[QuotaItem]


class Quota(TypedDict, total=False):
    """The quotas of the tool."""

    categories: list[QuotaCategory]


class QuotaResponse(TypedDict, total=False):
    """GET /quotas."""

    quota: Quota
    messages: ResponseMessages


class Health(TypedDict, total=False):
    """Health of the API itself."""

    status: Literal["OK", "ERROR"]
    message: str


class HealthResponse(TypedDict, total=False):
    """GET /jobs/v1/healthz."""

    health: Health
    messages: ResponseMessages


__all__ = [
    "EmailOption",
    "Health",
    "HealthCheck",
    "HealthResponse",
    "Image",
    "ImagesResponse",
    "Job",
    "JobListResponse",
    "JobResponse",
    "JobStatus",
    "JobStatusShort",
    "JobType",
    "MessagesResponse",
    "MountOption",
    "NewJob",
    "Quota",
    "QuotaCategory",
    "QuotaItem",
    "QuotaResponse",
    "ResponseMessages",
    "UpdateResponse",
]
