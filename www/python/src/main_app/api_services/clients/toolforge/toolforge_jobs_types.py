"""Response and request shapes of the Toolforge Jobs API.

Taken from the OpenAPI spec (Toolforge API 8.37.3). They are dataclasses; each one
has a ``load`` classmethod that builds it (and nested ones) from a plain dict
using ``dacite``.
Every field is optional and defaults to ``None`` (meaning "not present in the
payload"), which mirrors the former ``TypedDict(total=False)`` behaviour.
Endpoints that are not JSON return ``str`` instead:
- GET .../jobs/{id}/logs  -> text/plain
- GET /jobs/v1/metrics    -> text/plain
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, TypeVar

from dacite import Config, from_dict

JobType = Literal["one-off", "scheduled", "continuous", "webservice"]
JobStatusShort = Literal["pending", "running", "succeeded", "failed", "unknown"]
EmailOption = Literal["none", "all", "onfinish", "onfailure"]
MountOption = Literal["all", "none"]

_CONFIG = Config(check_types=True, strict=False)  # unknown API fields are ignored

T = TypeVar("T", bound="Helper")


@dataclass(kw_only=True)
class Helper:
    @classmethod
    def load(cls: type[T], data: dict[str, Any]) -> T:
        return from_dict(data_class=cls, data=data, config=_CONFIG)

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(kw_only=True)
class ResponseMessages(Helper):
    """Messages by priority, present in almost every response.

    Note: on success the API wraps it (``{"messages": {...}}``), but the 400/401/404
    error bodies ARE this object (``{"error": [...]}``). Which one to load is decided
    by the HTTP status code, see ToolforgeJobsService.
    """

    info: list[str] | None = None
    warning: list[str] | None = None
    error: list[str] | None = None


@dataclass(kw_only=True)
class JobStatus(Helper):
    """``job.status``: standardized status (``short`` and ``duration`` are always present)."""

    short: JobStatusShort | None = None
    duration: str | None = None  # e.g. "24d24h59m45s"
    messages: list[str] | None = None  # e.g. ["exitcode 127"]
    up_to_date: bool | None = None
    previous_schedule: str | None = None  # scheduled jobs only, ISO 8601
    next_schedule: str | None = None  # scheduled jobs only, ISO 8601


@dataclass(kw_only=True)
class HealthCheck(Helper):
    """``job.health_check``: ``script`` for type "script", ``path`` for type "http"."""

    type: Literal["script", "http"] | None = None
    script: str | None = None
    path: str | None = None


@dataclass(kw_only=True)
class ToolForgeJob(Helper):
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

    name: str | None = None  # 1-52 chars, lowercase, digits, "-" and "."
    imagename: str | None = None
    image: str | None = None
    image_state: str | None = None  # e.g. "stable"
    memory: str | None = None
    cpu: str | None = None
    emails: EmailOption | None = None
    mount: MountOption | None = None
    job_type: JobType | None = None
    cmd: str | None = None
    retry: int | None = None  # 0-5
    schedule: str | None = None
    schedule_actual: str | None = None
    timeout: int | None = None
    replicas: int | None = None
    port: int | None = None
    port_protocol: Literal["tcp", "udp"] | None = None
    publish: str | None = None
    continuous: bool | None = None
    health_check: HealthCheck | None = None
    filelog: bool | None = None
    filelog_stdout: str | None = None
    filelog_stderr: str | None = None
    status_short: str | None = None  # legacy text such as "Running."
    status_long: str | None = None  # legacy extended text
    status: JobStatus = field(default_factory=JobStatus)

    @property
    def health_check_text(self) -> None | str:
        if not self.health_check:
            return None

        target = self.health_check.script or self.health_check.path or ""
        return f"{self.health_check.type}: {target}".strip(": ")

    @property
    def status_key(self) -> str:
        """Return a lowercase short status: pending, running, succeeded, failed or unknown."""
        short = self.status.short or self.status_short or "unknown"
        # The legacy status_short is free text such as "Running."
        return str(short).lower().rstrip(".")

    def rows(self) -> list[Any]:
        status = self.status

        rows = [
            ("Status", self.status_key),
            ("Health check", self.health_check_text),
            ("Type", self.job_type),
            ("Duration", status.duration),
            ("Up to date", status.up_to_date),
            ("Schedule", self.schedule),
            ("Actual schedule", self.schedule_actual),
            ("Previous run", status.previous_schedule),
            ("Next run", status.next_schedule),
            ("Timeout (s)", self.timeout),
            ("Retry", self.retry),
            ("Replicas", self.replicas),
            ("Port", self.port),
            ("Protocol", self.port_protocol),
            ("Published path", self.publish),
            ("Image", self.image),
            ("Image state", self.image_state),
            ("Command", self.cmd),
            ("CPU", self.cpu),
            ("Memory", self.memory),
            ("Mount", self.mount),
            ("Emails", self.emails),
            ("Stdout log", self.filelog_stdout),
            ("Stderr log", self.filelog_stderr),
            ("Details", self.status_long),
        ]

        return rows


@dataclass(kw_only=True)
class NewJob(Helper):
    """Request body of create_job / update_job (a Job without the status fields).

    Required: ``name`` and ``imagename`` (``name`` defaults to "webservice" for
    webservice jobs), plus ``cmd`` for one-off/scheduled/continuous jobs,
    ``schedule`` for scheduled jobs and ``job_type`` for webservice jobs.
    """

    name: str | None = None
    imagename: str | None = None
    cmd: str | None = None
    job_type: JobType | None = None
    memory: str | None = None
    cpu: str | None = None
    emails: EmailOption | None = None
    mount: MountOption | None = None
    retry: int | None = None
    schedule: str | None = None
    timeout: int | None = None
    replicas: int | None = None
    port: int | None = None
    port_protocol: Literal["tcp", "udp"] | None = None
    publish: str | None = None
    continuous: bool | None = None
    health_check: HealthCheck | None = None
    filelog: bool | None = None
    filelog_stdout: str | None = None
    filelog_stderr: str | None = None


@dataclass(kw_only=True)
class JobListResponse(Helper):
    """GET /jobs."""

    jobs: list[ToolForgeJob] | None = None
    messages: ResponseMessages | None = None


@dataclass(kw_only=True)
class JobResponse(Helper):
    """GET /jobs/{id} and POST /jobs."""

    job: ToolForgeJob | None = None
    messages: ResponseMessages | None = None


@dataclass(kw_only=True)
class MessagesResponse(Helper):
    """DELETE /jobs, DELETE /jobs/{id} and POST /jobs/{id}/restart."""

    messages: ResponseMessages | None = None


@dataclass(kw_only=True)
class UpdateResponse(Helper):
    """PATCH /jobs."""

    messages: ResponseMessages | None = None
    job_changed: bool | None = None


@dataclass(kw_only=True)
class Image(Helper):
    """One entry of the images list."""

    shortname: str | None = None
    image: str | None = None


@dataclass(kw_only=True)
class ImagesResponse(Helper):
    """GET /images."""

    images: list[Image] | None = None
    messages: ResponseMessages | None = None


@dataclass(kw_only=True)
class QuotaItem(Helper):
    """One quota line; ``limit`` and ``used`` are strings (e.g. "1G")."""

    name: str | None = None
    limit: str | None = None
    used: str | None = None


@dataclass(kw_only=True)
class QuotaCategory(Helper):
    """A group of quota lines."""

    name: str | None = None
    items: list[QuotaItem] | None = None


@dataclass(kw_only=True)
class Quota(Helper):
    """The quotas of the tool."""

    categories: list[QuotaCategory] | None = None


@dataclass(kw_only=True)
class QuotaResponse(Helper):
    """GET /quotas."""

    quota: Quota | None = None
    messages: ResponseMessages | None = None


@dataclass(kw_only=True)
class Health(Helper):
    """Health of the API itself."""

    status: Literal["OK", "ERROR"] | None = None
    message: str | None = None


@dataclass(kw_only=True)
class HealthResponse(Helper):
    """GET /jobs/v1/healthz."""

    health: Health | None = None
    messages: ResponseMessages | None = None


__all__ = [
    "EmailOption",
    "Health",
    "HealthCheck",
    "HealthResponse",
    "Helper",
    "Image",
    "ImagesResponse",
    "ToolForgeJob",
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
