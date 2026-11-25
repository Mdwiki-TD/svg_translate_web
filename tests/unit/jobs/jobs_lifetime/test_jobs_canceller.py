"""Tests for ``jobs_lifetime.jobs_canceller.JobCanceller``."""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from src.main_app.jobs.jobs_lifetime.jobs_canceller import JobCanceller
from src.main_app.jobs.utils import generate_cancelled_file_name


@dataclass
class MockCancellerParts:
    canceller: JobCanceller
    files_service: MagicMock
    jobs_service: MagicMock
    backend_registry: MagicMock
    backend: MagicMock


@pytest.fixture
def parts(mock_jobs_service: MagicMock) -> MockCancellerParts:
    files_service = MagicMock()

    backend = MagicMock()
    backend.cancel.return_value = True

    backend_registry = MagicMock()
    backend_registry.get_backend.return_value = backend

    mock_jobs_service.cancel_job_db.return_value = True

    return MockCancellerParts(
        canceller=JobCanceller(files_service, mock_jobs_service, backend_registry),
        files_service=files_service,
        jobs_service=mock_jobs_service,
        backend_registry=backend_registry,
        backend=backend,
    )


class TestJobLookup:
    def test_loads_the_job_when_only_the_id_is_given(self, parts: MockCancellerParts, make_job_record) -> None:
        job = make_job_record(backend="toolforge", result_file="demo_job_7.json")
        parts.jobs_service.get_by.return_value = job

        assert parts.canceller.cancel(7) is True

        parts.jobs_service.get_by.assert_called_once_with(id=7)
        parts.backend_registry.get_backend.assert_called_once_with("toolforge")
        parts.backend.cancel.assert_called_once_with(job)

    def test_does_not_reload_a_job_that_was_passed_in(self, parts: MockCancellerParts, job_record) -> None:
        parts.canceller.cancel(7, job=job_record)

        parts.jobs_service.get_by.assert_not_called()

    def test_unknown_job_only_touches_the_database(self, parts: MockCancellerParts) -> None:
        parts.jobs_service.get_by.return_value = None

        assert parts.canceller.cancel(99) is True

        parts.jobs_service.cancel_job_db.assert_called_once_with(99, None)
        parts.files_service.create_cancel_file.assert_not_called()
        parts.backend_registry.get_backend.assert_not_called()

    def test_job_type_defaults_to_the_jobs_own_type(self, parts: MockCancellerParts, job_record) -> None:
        parts.canceller.cancel(7, job=job_record)

        parts.jobs_service.cancel_job_db.assert_called_once_with(7, "demo")

    def test_explicit_job_type_is_kept(self, parts: MockCancellerParts, job_record) -> None:
        parts.canceller.cancel(7, job_type="other", job=job_record)

        parts.jobs_service.cancel_job_db.assert_called_once_with(7, "other")


class TestCancelFile:
    def test_uses_the_result_file_when_the_job_has_one(self, parts: MockCancellerParts, make_job_record) -> None:
        job = make_job_record(result_file="custom_result.json")

        parts.canceller.cancel(7, job=job)

        parts.files_service.create_cancel_file.assert_called_once_with(
            generate_cancelled_file_name(result_file="custom_result.json")
        )

    def test_pending_job_without_result_file_still_gets_a_cancel_file(
        self,
        parts: MockCancellerParts,
        make_job_record,
    ) -> None:
        job = make_job_record(result_file=None)

        parts.canceller.cancel(7, job=job)

        parts.files_service.create_cancel_file.assert_called_once_with(
            generate_cancelled_file_name(job_id=7, job_type="demo")
        )

    def test_file_errors_do_not_stop_the_backend_cancel(self, parts: MockCancellerParts, job_record) -> None:
        parts.files_service.create_cancel_file.side_effect = OSError("disk full")

        assert parts.canceller.cancel(7, job=job_record) is True

        parts.backend.cancel.assert_called_once_with(job_record)


class TestBackendCancel:
    @pytest.mark.parametrize(
        ("job_backend", "expected_name"),
        [("thread", "thread"), ("toolforge", "toolforge"), (None, "thread")],
    )
    def test_uses_the_backend_that_runs_the_job(
        self,
        parts: MockCancellerParts,
        make_job_record,
        job_backend: str | None,
        expected_name: str,
    ) -> None:
        parts.canceller.cancel(7, job=make_job_record(backend=job_backend))

        parts.backend_registry.get_backend.assert_called_once_with(expected_name)

    def test_database_is_cancelled_before_the_backend(self, parts: MockCancellerParts, job_record) -> None:
        order: list[str] = []
        parts.jobs_service.cancel_job_db.side_effect = lambda *args: order.append("db") or True
        parts.backend.cancel.side_effect = lambda *args: order.append("backend") or True

        parts.canceller.cancel(7, job=job_record)

        assert order == ["db", "backend"]

    def test_backend_failure_is_swallowed(self, parts: MockCancellerParts, job_record) -> None:
        parts.backend.cancel.side_effect = RuntimeError("api down")

        assert parts.canceller.cancel(7, job=job_record) is True

    def test_database_failure_is_swallowed_and_other_channels_still_run(
        self,
        parts: MockCancellerParts,
        job_record,
    ) -> None:
        parts.jobs_service.cancel_job_db.side_effect = RuntimeError("db down")

        assert parts.canceller.cancel(7, job=job_record) is True

        parts.backend.cancel.assert_called_once_with(job_record)
        parts.files_service.create_cancel_file.assert_called_once()


class TestResult:
    def test_false_when_no_channel_accepted_the_request(self, parts: MockCancellerParts, job_record) -> None:
        parts.jobs_service.cancel_job_db.return_value = False
        parts.files_service.create_cancel_file.return_value = None
        parts.backend.cancel.return_value = False

        assert parts.canceller.cancel(7, job=job_record) is False

    @pytest.mark.parametrize("channel", ["db", "file", "backend"])
    def test_true_when_any_single_channel_accepted(
        self,
        parts: MockCancellerParts,
        job_record,
        channel: str,
    ) -> None:
        parts.jobs_service.cancel_job_db.return_value = channel == "db"
        parts.files_service.create_cancel_file.return_value = "path" if channel == "file" else None
        parts.backend.cancel.return_value = channel == "backend"

        assert parts.canceller.cancel(7, job=job_record) is True
