"""Tests for ``jobs_lifetime.job_creator``."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from src.main_app.database.exceptions import DuplicateRecordError
from src.main_app.jobs.jobs_lifetime.job_creator import (
    CreatedJob,
    JobCreator,
    _load_job_args,
    _sanitize_args,
)

MODULE = "src.main_app.jobs.jobs_lifetime.job_creator"


@pytest.fixture
def mock_load_job_data(monkeypatch: pytest.MonkeyPatch, job_data) -> MagicMock:
    _mock = MagicMock(side_effect=lambda job_type: job_data if job_type == job_data.job_type else None)
    monkeypatch.setattr(f"{MODULE}.load_job_data", _mock)
    return _mock


@pytest.fixture
def mock_settings_service_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = MagicMock()
    _mock_instance = MagicMock()
    _mock_instance.get_all_settings_ready.return_value = {}
    _mock_class.return_value = _mock_instance
    monkeypatch.setattr(f"{MODULE}.SettingsService", _mock_class)
    return _mock_class


@pytest.fixture
def creator(mock_jobs_service: MagicMock, job_record, mock_load_job_data: MagicMock) -> JobCreator:
    mock_jobs_service.create_job.return_value = job_record
    return JobCreator(mock_jobs_service)


class TestSanitizeArgs:
    def test_removes_csrf_token(self) -> None:
        assert _sanitize_args({"csrf_token": "x", "keep": 1}) == {"keep": 1}

    def test_does_not_mutate_the_input(self) -> None:
        original = {"csrf_token": "x", "keep": 1}

        _sanitize_args(original)

        assert original == {"csrf_token": "x", "keep": 1}


class TestLoadJobArgs:
    def test_empty_definition_does_not_touch_settings(self, mock_settings_service_class: MagicMock) -> None:
        assert _load_job_args([]) == {}
        mock_settings_service_class.assert_not_called()

    def test_maps_setting_keys_to_argument_names_and_skips_none(self, mock_settings_service_class: MagicMock) -> None:
        mock_settings_service_class.return_value.get_all_settings_ready.return_value = {
            "limit": 5,
            "empty": None,
        }

        result = _load_job_args(
            [
                {"key": "limit", "as": "limit_items"},
                {"key": "empty", "as": "ignored"},
                {"key": "absent", "as": "also_ignored"},
            ]
        )

        assert result == {"limit_items": 5}


class TestCreate:
    def test_unknown_job_type(self, creator: JobCreator) -> None:
        with pytest.raises(ValueError, match="Unknown job type"):
            creator.create(username="alice", job_type="nope", backend_name="thread")

    def test_missing_username(self, creator: JobCreator) -> None:
        with pytest.raises(ValueError, match="authentication"):
            creator.create(username="", job_type="demo", backend_name="thread")

    def test_returns_created_job_with_the_saved_payload(
        self,
        creator: JobCreator,
        mock_jobs_service: MagicMock,
        job_record,
        job_data,
    ) -> None:
        created = creator.create(
            username="alice",
            job_type="demo",
            backend_name="thread",
            args={"keep": 1},
            form_data={"f": 1},
        )

        assert isinstance(created, CreatedJob)
        assert created.job is job_record
        assert created.job_data is job_data
        assert created.payload == {"args": {"keep": 1}, "form_data": {"f": 1}}
        mock_jobs_service.create_job.assert_called_once_with("demo", "alice")
        mock_jobs_service.save_payload.assert_called_once_with(7, "thread", created.payload)

    def test_payload_never_contains_user_data_and_drops_csrf(self, creator: JobCreator) -> None:
        created = creator.create(
            username="alice",
            job_type="demo",
            backend_name="thread",
            args={"csrf_token": "x", "keep": 1},
        )

        assert "user" not in created.payload
        assert created.payload["args"] == {"keep": 1}

    def test_explicit_args_override_settings_args(
        self,
        creator: JobCreator,
        job_data,
        mock_settings_service_class: MagicMock,
    ) -> None:
        job_data.job_args = [{"key": "limit", "as": "limit_items"}]
        mock_settings_service_class.return_value.get_all_settings_ready.return_value = {"limit": 5}

        created = creator.create(
            username="alice",
            job_type="demo",
            backend_name="thread",
            args={"limit_items": 99},
        )

        assert created.payload["args"] == {"limit_items": 99}

    def test_duplicate_is_reraised_and_nothing_is_saved(
        self,
        creator: JobCreator,
        mock_jobs_service: MagicMock,
    ) -> None:
        mock_jobs_service.create_job.side_effect = DuplicateRecordError()

        with pytest.raises(DuplicateRecordError):
            creator.create(username="alice", job_type="demo", backend_name="thread")

        mock_jobs_service.save_payload.assert_not_called()

    def test_unexpected_create_error_is_reraised(
        self,
        creator: JobCreator,
        mock_jobs_service: MagicMock,
    ) -> None:
        mock_jobs_service.create_job.side_effect = RuntimeError("db down")

        with pytest.raises(RuntimeError, match="db down"):
            creator.create(username="alice", job_type="demo", backend_name="thread")

        mock_jobs_service.save_payload.assert_not_called()
