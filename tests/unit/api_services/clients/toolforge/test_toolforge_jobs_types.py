"""Tests for the ``load`` classmethods of toolforge_jobs_types (they use dacite)."""

from __future__ import annotations

import dataclasses

import pytest
import src.main_app.api_services.clients.toolforge.toolforge_jobs_types as t
from dacite import DaciteError

# Helper is the shared base class, not one of the API shapes.
ALL_CLASSES = [
    obj
    for obj in vars(t).values()
    if dataclasses.is_dataclass(obj) and isinstance(obj, type) and obj is not t.Helper and obj.__name__ != "Config"
]


# ---------------------------------------------------------------------------
# Generic behaviour for every dataclass
# ---------------------------------------------------------------------------


def test_all_dataclasses_were_discovered() -> None:
    assert len(ALL_CLASSES) == 17


@pytest.mark.parametrize("cls", ALL_CLASSES, ids=lambda c: c.__name__)
def test_has_load_classmethod(cls: type) -> None:
    assert callable(getattr(cls, "load", None)), f"{cls.__name__} has no load()"


@pytest.mark.parametrize("cls", ALL_CLASSES, ids=lambda c: c.__name__)
def test_load_empty_dict_gives_all_none(cls: type) -> None:
    obj = cls.load({})
    assert isinstance(obj, cls)
    for field in dataclasses.fields(cls):
        if field.default_factory is not dataclasses.MISSING:  # e.g. ToolForgeJob.status
            assert getattr(obj, field.name) == field.default_factory()
        else:
            assert getattr(obj, field.name) is None


@pytest.mark.parametrize("cls", ALL_CLASSES, ids=lambda c: c.__name__)
def test_load_ignores_unknown_fields(cls: type) -> None:
    obj = cls.load({"some_new_field_from_the_api": 123})
    assert isinstance(obj, cls)
    assert not hasattr(obj, "some_new_field_from_the_api")


# ---------------------------------------------------------------------------
# Simple classes
# ---------------------------------------------------------------------------


def test_response_messages() -> None:
    obj = t.ResponseMessages.load({"info": ["a"], "warning": ["b", "c"], "error": []})
    assert obj.info == ["a"]
    assert obj.warning == ["b", "c"]
    assert obj.error == []


def test_tool_forge_job_status_defaults_to_an_empty_job_status() -> None:
    job = t.ToolForgeJob.load({"name": "x"})
    assert job.status == t.JobStatus()
    assert job.status_key == "unknown"


def test_bare_error_body_is_a_response_messages_not_a_messages_response() -> None:
    """4xx bodies are a bare ResponseMessages; MessagesResponse would silently drop them."""
    body = {"error": ["Unable to restart a one-off job"]}

    assert t.ResponseMessages.load(body).error == ["Unable to restart a one-off job"]
    assert t.MessagesResponse.load(body).messages is None  # the shape is not guessed


def test_job_status_scheduled() -> None:
    obj = t.JobStatus.load(
        {
            "short": "running",
            "duration": "24d24h59m45s",
            "messages": ["exitcode 127"],
            "up_to_date": True,
            "previous_schedule": "2025-08-27T10:07:48Z",
            "next_schedule": "2025-08-28T10:07:48Z",
        }
    )
    assert obj.short == "running"
    assert obj.duration == "24d24h59m45s"
    assert obj.messages == ["exitcode 127"]
    assert obj.up_to_date is True
    assert obj.next_schedule == "2025-08-28T10:07:48Z"


def test_job_status_invalid_literal() -> None:
    with pytest.raises(DaciteError):
        t.JobStatus.load({"short": "exploded"})


@pytest.mark.parametrize(
    "data",
    [
        {"type": "script", "script": "test -e /tmp/ok"},
        {"type": "http", "path": "/healthz"},
    ],
)
def test_health_check(data: dict) -> None:
    obj = t.HealthCheck.load(data)
    assert obj.type == data["type"]
    assert obj.script == data.get("script")
    assert obj.path == data.get("path")


def test_health_check_invalid_type() -> None:
    with pytest.raises(DaciteError):
        t.HealthCheck.load({"type": "tcp"})


def test_wrong_field_type_raises() -> None:
    with pytest.raises(DaciteError):
        t.ToolForgeJob.load({"name": 123})


def test_image() -> None:
    obj = t.Image.load({"shortname": "python3.11", "image": "docker-registry/python:3.11"})
    assert obj.shortname == "python3.11"
    assert obj.image == "docker-registry/python:3.11"


def test_health() -> None:
    assert t.Health.load({"status": "OK", "message": "fine"}).status == "OK"
    with pytest.raises(DaciteError):
        t.Health.load({"status": "MAYBE"})


# ---------------------------------------------------------------------------
# ToolForgeJob / NewJob
# ---------------------------------------------------------------------------

SCHEDULED_JOB = {
    "name": "my-job",
    "imagename": "python3.11",
    "image": "docker-registry/python:3.11",
    "image_state": "stable",
    "memory": "1G",
    "cpu": "1",
    "emails": "onfailure",
    "mount": "all",
    "job_type": "scheduled",
    "cmd": "./run.sh",
    "retry": 2,
    "schedule": "@hourly",
    "schedule_actual": "15 * * * *",
    "timeout": 120,
    "filelog": True,
    "filelog_stdout": "logs/my-job.out",
    "filelog_stderr": "logs/my-job.err",
    "status_short": "Running.",
    "status_long": "Running since 30 seconds ago.",
    "status": {
        "short": "running",
        "duration": "30s",
        "next_schedule": "2025-08-28T10:07:48Z",
    },
}


def test_tool_forge_job_scheduled_with_nested_status() -> None:
    job = t.ToolForgeJob.load(SCHEDULED_JOB)
    assert job.name == "my-job"
    assert job.job_type == "scheduled"
    assert job.retry == 2
    assert job.timeout == 120
    assert job.schedule_actual == "15 * * * *"
    assert isinstance(job.status, t.JobStatus)
    assert job.status.short == "running"
    assert job.status.next_schedule == "2025-08-28T10:07:48Z"
    # fields that do not apply to this job type stay None
    assert job.replicas is None
    assert job.health_check is None


def test_tool_forge_job_continuous_with_health_check() -> None:
    job = t.ToolForgeJob.load(
        {
            "name": "web",
            "imagename": "node18",
            "job_type": "continuous",
            "cmd": "node app.js",
            "continuous": True,
            "replicas": 2,
            "port": 8080,
            "port_protocol": "tcp",
            "publish": "/",
            "health_check": {"type": "http", "path": "/healthz"},
        }
    )
    assert job.replicas == 2
    assert job.port == 8080
    assert job.publish == "/"
    assert isinstance(job.health_check, t.HealthCheck)
    assert job.health_check.path == "/healthz"


def test_tool_forge_job_nullable_fields_accept_none() -> None:
    job = t.ToolForgeJob.load(
        {
            "name": "x",
            "memory": None,
            "cpu": None,
            "timeout": None,
            "replicas": None,
            "port": None,
            "health_check": None,
            "filelog_stdout": None,
            "filelog_stderr": None,
        }
    )
    assert job.name == "x"
    assert job.memory is None
    assert job.health_check is None


def test_tool_forge_job_invalid_enum_values() -> None:
    for field, bad in [("job_type", "cron"), ("emails", "sometimes"), ("mount", "some")]:
        with pytest.raises(DaciteError):
            t.ToolForgeJob.load({field: bad})


def test_new_job_webservice() -> None:
    job = t.NewJob.load(
        {
            "imagename": "python3.11",
            "job_type": "webservice",
            "port": 8000,
            "replicas": 1,
            "health_check": {"type": "script", "script": "test -e /tmp/ok"},
        }
    )
    assert job.name is None  # server defaults it to "webservice"
    assert job.job_type == "webservice"
    assert isinstance(job.health_check, t.HealthCheck)
    assert job.health_check.script == "test -e /tmp/ok"


# ---------------------------------------------------------------------------
# Response wrappers
# ---------------------------------------------------------------------------


def test_job_list_response() -> None:
    resp = t.JobListResponse.load(
        {
            "jobs": [SCHEDULED_JOB, {"name": "other", "job_type": "one-off", "cmd": "ls"}],
            "messages": {"warning": ["deprecated"]},
        }
    )
    assert resp.jobs is not None and len(resp.jobs) == 2
    assert all(isinstance(j, t.ToolForgeJob) for j in resp.jobs)
    assert resp.jobs[0].status is not None and resp.jobs[0].status.short == "running"
    assert resp.jobs[1].job_type == "one-off"
    assert isinstance(resp.messages, t.ResponseMessages)
    assert resp.messages.warning == ["deprecated"]


def test_job_response() -> None:
    resp = t.JobResponse.load({"job": SCHEDULED_JOB, "messages": {"info": ["ok"]}})
    assert isinstance(resp.job, t.ToolForgeJob)
    assert resp.job.name == "my-job"
    assert resp.messages is not None and resp.messages.info == ["ok"]


def test_messages_response() -> None:
    resp = t.MessagesResponse.load({"messages": {"error": ["boom"]}})
    assert resp.messages is not None and resp.messages.error == ["boom"]


def test_update_response() -> None:
    resp = t.UpdateResponse.load({"job_changed": True, "messages": {"info": []}})
    assert resp.job_changed is True
    assert isinstance(resp.messages, t.ResponseMessages)


def test_images_response() -> None:
    resp = t.ImagesResponse.load(
        {
            "images": [
                {"shortname": "bash", "image": "reg/bash:5"},
                {"shortname": "php8.2", "image": "reg/php:8.2"},
            ]
        }
    )
    assert resp.images is not None
    assert [i.shortname for i in resp.images] == ["bash", "php8.2"]
    assert all(isinstance(i, t.Image) for i in resp.images)


def test_quota_response_deeply_nested() -> None:
    resp = t.QuotaResponse.load(
        {
            "quota": {
                "categories": [
                    {
                        "name": "Basic",
                        "items": [
                            {"name": "Running jobs", "limit": "10", "used": "3"},
                            {"name": "Memory", "limit": "1G", "used": "512M"},
                        ],
                    },
                    {"name": "Empty", "items": []},
                ]
            },
            "messages": {"info": ["hi"]},
        }
    )
    assert isinstance(resp.quota, t.Quota)
    assert resp.quota.categories is not None
    cat = resp.quota.categories[0]
    assert isinstance(cat, t.QuotaCategory)
    assert cat.name == "Basic"
    assert cat.items is not None and isinstance(cat.items[1], t.QuotaItem)
    assert cat.items[1].limit == "1G"
    assert resp.quota.categories[1].items == []


def test_quota_item_requires_string_values() -> None:
    with pytest.raises(DaciteError):
        t.QuotaItem.load({"name": "x", "limit": 10, "used": 3})


def test_health_response() -> None:
    resp = t.HealthResponse.load(
        {"health": {"status": "ERROR", "message": "db down"}, "messages": {"error": ["db down"]}}
    )
    assert isinstance(resp.health, t.Health)
    assert resp.health.status == "ERROR"
    assert resp.messages is not None and resp.messages.error == ["db down"]


# ---------------------------------------------------------------------------
# Round trip
# ---------------------------------------------------------------------------


def test_round_trip_through_asdict() -> None:
    job = t.ToolForgeJob.load(SCHEDULED_JOB)
    again = t.ToolForgeJob.load(dataclasses.asdict(job))
    assert again == job
