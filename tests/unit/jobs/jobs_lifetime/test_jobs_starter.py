"""Tests for ``jobs_lifetime.jobs_starter.JobStarter``."""

from __future__ import annotations

import json
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from src.main_app.jobs.jobs_lifetime.job_creator import CreatedJob
from src.main_app.jobs.jobs_lifetime.jobs_starter import INLINE_BACKEND_NAME, JobStarter


@dataclass
class MockStarterParts:
    starter: JobStarter
    creator: MagicMock
    executor: MagicMock
    backend_registry: MagicMock
    backend: MagicMock


@pytest.fixture
def parts(job_record, job_data, mock_jobs_service: MagicMock) -> MockStarterParts:
    creator = MagicMock()
    creator.create.return_value = CreatedJob(job=job_record, job_data=job_data, payload={})

    executor = MagicMock()
    executor.run.return_value = 0

    backend = MagicMock()
    backend_registry = MagicMock()
    backend_registry.get_backend_name.return_value = "thread"
    backend_registry.get_backend.return_value = backend

    starter = JobStarter(
        jobs_service=mock_jobs_service,
        creator=creator,
        executor=executor,
        backend_registry=backend_registry,
    )
    return MockStarterParts(
        starter=starter,
        creator=creator,
        executor=executor,
        backend_registry=backend_registry,
        backend=backend,
    )


class TestStart:
    def test_creates_the_job_then_hands_it_to_the_backend(self, parts: MockStarterParts, job_record, job_data) -> None:
        auth = {"username": "alice", "access_token": "secret"}

        job_id = parts.starter.start(auth, "demo", {"a": 1})

        assert job_id == 7
        create_kwargs = parts.creator.create.call_args.kwargs
        assert create_kwargs["username"] == "alice"
        assert create_kwargs["job_type"] == "demo"
        assert create_kwargs["backend_name"] == "thread"
        assert create_kwargs["args"] == {"a": 1}
        parts.backend.start.assert_called_once_with(job_record, job_data, user=auth)
        parts.backend_registry.get_backend.assert_called_once_with("thread")

    def test_user_token_is_only_given_to_the_backend_never_to_the_creator(self, parts: MockStarterParts) -> None:
        parts.starter.start({"username": "alice", "access_token": "secret"}, "demo")

        assert "secret" not in json.dumps(parts.creator.create.call_args.kwargs, default=str)

    def test_never_runs_the_job_inline(self, parts: MockStarterParts) -> None:
        parts.starter.start({"username": "alice"}, "demo")

        parts.executor.run.assert_not_called()

    @pytest.mark.parametrize("auth", [None, {}, {"username": ""}])
    def test_requires_a_username(self, parts: MockStarterParts, auth) -> None:
        with pytest.raises(ValueError, match="authentication"):
            parts.starter.start(auth, "demo")

        parts.creator.create.assert_not_called()

class TestSubmitForm:
    def test_passes_form_data_to_the_creator(self, parts: MockStarterParts) -> None:
        parts.starter.start({"username": "alice"}, "demo", {"a": 1}, {"f": 1})

        assert parts.creator.create.call_args.kwargs["form_data"] == {"f": 1}
        parts.backend.start.assert_called_once()


class TestRunNow:
    def test_runs_inline_with_the_system_user_and_no_backend(self, parts: MockStarterParts) -> None:
        exit_code = parts.starter.run_now("demo", {"update_all": "true"})

        assert exit_code == 0
        create_kwargs = parts.creator.create.call_args.kwargs
        assert create_kwargs["username"] == "Background job"
        assert create_kwargs["backend_name"] == INLINE_BACKEND_NAME
        assert create_kwargs["args"] == {"update_all": "true"}
        parts.backend.start.assert_not_called()
        parts.backend_registry.get_backend.assert_not_called()

    def test_executor_gets_the_job_id_user_and_signal_handlers(self, parts: MockStarterParts) -> None:
        parts.starter.run_now("demo")

        parts.executor.run.assert_called_once_with(
            7,
            user={"username": "Background job"},
            install_signal_handlers=True,
        )

    def test_custom_user_and_no_signal_handlers(self, parts: MockStarterParts) -> None:
        parts.starter.run_now("demo", user={"username": "bot"}, install_signal_handlers=False)

        assert parts.creator.create.call_args.kwargs["username"] == "bot"
        assert parts.executor.run.call_args.kwargs == {
            "user": {"username": "bot"},
            "install_signal_handlers": False,
        }

    def test_propagates_the_executor_exit_code(self, parts: MockStarterParts) -> None:
        parts.executor.run.return_value = 1

        assert parts.starter.run_now("demo") == 1
