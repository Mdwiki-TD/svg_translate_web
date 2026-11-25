"""Shared fixtures for the jobs test-suite (``tests/unit/jobs/**``)."""

from __future__ import annotations

import json
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from flask import Flask
from src.main_app.jobs_workers.objects import JobData


@pytest.fixture
def make_job_record() -> Callable[..., SimpleNamespace]:
    """Factory for ``JobRecord``-like objects; override only the fields a test cares about."""

    def _factory(**overrides: Any) -> SimpleNamespace:
        fields: dict[str, Any] = {
            "id": 7,
            "job_type": "demo",
            "username": "alice",
            "status": "pending",
            "payload": json.dumps({"args": {"a": 1}, "form_data": {"f": 2}}),
            "result_file": None,
            "backend": "thread",
            "created_at": None,
        }
        fields.update(overrides)
        return SimpleNamespace(**fields)

    return _factory


@pytest.fixture
def job_record(make_job_record: Callable[..., SimpleNamespace]) -> SimpleNamespace:
    return make_job_record()


@pytest.fixture
def fake_worker_cls() -> type:
    """A fresh worker class per test, so recorded instances never leak between tests.

    Set ``fake_worker_cls.behaviour`` to ``"run_error"`` or ``"ctor_error"`` to make it fail.
    """

    class FakeWorker:
        instances: list[FakeWorker] = []
        behaviour = "ok"

        def __init__(self, runner: Any) -> None:
            if type(self).behaviour == "ctor_error":
                raise RuntimeError("boom in constructor")
            self.runner = runner
            type(self).instances.append(self)

        def run(self) -> dict[str, Any]:
            if type(self).behaviour == "run_error":
                raise RuntimeError("boom in run")
            return {}

    return FakeWorker


@pytest.fixture
def job_data(fake_worker_cls: type) -> JobData:
    return JobData(
        job_type="demo",
        job_name="Demo",
        job_class=fake_worker_cls,
        job_for_admin=True,
    )


@pytest.fixture
def mock_jobs_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def flask_app() -> Flask:
    return Flask("jobs-tests")
