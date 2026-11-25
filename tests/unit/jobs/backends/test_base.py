"""Tests for the ``JobBackend`` abstract interface."""

from __future__ import annotations

import pytest
from src.main_app.jobs.backends.base import JobBackend


@pytest.fixture
def minimal_backend_cls() -> type[JobBackend]:
    class MinimalBackend(JobBackend):
        def start(self, job, job_data, user=None) -> str:
            return "id"

        def cancel(self, job) -> bool:
            return True

    return MinimalBackend


class TestJobBackend:
    def test_cannot_be_instantiated_directly(self) -> None:
        with pytest.raises(TypeError):
            JobBackend()  # type: ignore[abstract]

    def test_start_and_cancel_are_required(self) -> None:
        class OnlyStart(JobBackend):
            def start(self, job, job_data, user=None) -> str:
                return "id"

        with pytest.raises(TypeError):
            OnlyStart()  # type: ignore[abstract]

    def test_status_defaults_to_none(self, minimal_backend_cls: type[JobBackend], job_record) -> None:
        assert minimal_backend_cls().status(job_record) is None

    def test_logs_default_to_empty(self, minimal_backend_cls: type[JobBackend], job_record) -> None:
        assert minimal_backend_cls().logs(job_record) == ""
        assert minimal_backend_cls().logs(job_record, tail=5) == ""

    def test_start_may_be_called_without_a_user(
        self, minimal_backend_cls: type[JobBackend], job_record, job_data
    ) -> None:
        assert minimal_backend_cls().start(job_record, job_data) == "id"
