"""Unit tests for copy_svg_langs worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker import (
    CopySvgLangsWorker,
    copy_svg_langs_worker_entry,
)


@pytest.fixture
def mock_worker_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = MagicMock()
    _mock_instance = MagicMock()
    _mock_class.return_value = _mock_instance
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.CopySvgLangsWorker",
        _mock_class,
    )
    return _mock_class


class TestCopySvgLangsWorker:
    def test_get_job_type(self) -> None:
        worker = CopySvgLangsWorker(
            job_id=1,
            user=None,
            args={"title": "Test.svg"},
        )
        assert worker.get_job_type() == "copy_svg_langs"

    def test_initial_result_structure(self) -> None:
        worker = CopySvgLangsWorker(
            job_id=1,
            user=None,
            args={"title": "Test.svg"},
        )
        result = worker.result

        assert result.status == "pending"
        assert result.started_at is not None
        assert result.completed_at is None
        assert result.cancelled_at is None
        assert result.title is None
        assert result.stages.text.status == "Pending"
        assert result.stages.titles.status == "Pending"
        assert result.stages.translations.status == "Pending"
        assert result.stages.download.status == "Pending"
        assert result.stages.nested.status == "Pending"
        assert result.stages.inject.status == "Pending"
        assert result.stages.upload.status == "Pending"

    def test_worker_init_with_user(self) -> None:
        user = {"username": "testuser", "id": 123}
        worker = CopySvgLangsWorker(
            job_id=1,
            args={"title": "Test.svg"},
            user=user,
        )
        assert worker.user == user

    def test_worker_init_with_cancel_event(self) -> None:
        cancel_event = threading.Event()
        worker = CopySvgLangsWorker(
            job_id=1,
            user=None,
            args={"title": "Test.svg"},
            cancel_event=cancel_event,
        )
        assert worker.cancel_event is cancel_event

    def test_worker_reads_upload_limit_from_args(self) -> None:
        worker = CopySvgLangsWorker(
            job_id=1,
            user=None,
            args={"title": "Test.svg", "upload_limit": 5},
        )
        assert worker.upload_limit == 5

    def test_worker_defaults_upload_limit_when_args_none(self) -> None:
        worker = CopySvgLangsWorker(
            job_id=1,
            user=None,
            args=None,
        )
        assert worker.upload_limit == 0

    def test_worker_upload_limit_none_when_key_missing(self) -> None:
        worker = CopySvgLangsWorker(
            job_id=1,
            user=None,
            args={"title": "Test.svg"},
        )
        assert worker.upload_limit == 0


class TestCopySvgLangsWorkerEntry:
    def test_worker_entry_missing_title(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(
            job_id=1,
            args={"title": ""},
            user=None,
        )

    def test_worker_entry_missing_args(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(
            job_id=1,
            args={"title": "Test.svg"},
            user=None,
        )

    def test_worker_entry_creates_worker(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(
            job_id=123,
            args={"title": "Test.svg"},
            user={"id": 1},
        )

        mock_worker_class.assert_called_once_with(
            job_id=123,
            args={"title": "Test.svg"},
            user={"id": 1},
            cancel_event=None,
        )
        mock_worker_class.return_value.run.assert_called_once()

    def test_worker_entry_with_cancel_event(self, mock_worker_class) -> None:
        cancel_event = threading.Event()

        copy_svg_langs_worker_entry(
            job_id=456,
            args={"title": "Another.svg"},
            user=None,
            cancel_event=cancel_event,
        )

        _, kwargs = mock_worker_class.call_args
        assert kwargs["cancel_event"] is cancel_event

    def test_worker_entry_args_is_keyword_only(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(job_id=1, user=None, args={"title": "Test.svg"})

        mock_worker_class.assert_called_once_with(
            job_id=1,
            args={"title": "Test.svg"},
            user=None,
            cancel_event=None,
        )
        mock_worker_class.return_value.run.assert_called_once()

    def test_worker_entry_args_defaults_to_none(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(job_id=99, user={"username": "tester"})

        mock_worker_class.assert_called_once_with(
            job_id=99,
            args=None,
            user={"username": "tester"},
            cancel_event=None,
        )

    def test_worker_entry_user_is_second_positional(self, mock_worker_class) -> None:
        user = {"username": "testuser"}

        copy_svg_langs_worker_entry(job_id=123, user=user)

        call_kwargs = mock_worker_class.call_args.kwargs
        assert call_kwargs["user"] is user

    def test_worker_entry_maps_copy_svg_langs_upload_limit(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(
            job_id=1,
            user=None,
            args={"upload_limit": 5},
        )

        call_kwargs = mock_worker_class.call_args.kwargs
        assert call_kwargs["args"]["upload_limit"] == 5

    def test_worker_entry_does_not_map_when_key_absent(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(
            job_id=1,
            user=None,
            args={"other_key": "value"},
        )

        call_kwargs = mock_worker_class.call_args.kwargs
        assert "upload_limit" not in call_kwargs["args"]

    def test_worker_entry_does_not_modify_args_when_none(self, mock_worker_class) -> None:
        copy_svg_langs_worker_entry(job_id=1, user=None, args=None)

        call_kwargs = mock_worker_class.call_args.kwargs
        assert call_kwargs["args"] is None
