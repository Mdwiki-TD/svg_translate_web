"""Unit tests for copy_svg_langs worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.runner import (
    copy_svg_langs_worker_entry,
)


@pytest.fixture
def mock_worker_class(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = MagicMock()
    _mock_instance = MagicMock()
    _mock_class.return_value = _mock_instance
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.runner.CopySvgLangsWorker",
        _mock_class,
    )
    return _mock_class


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
        with pytest.raises(TypeError):
            copy_svg_langs_worker_entry(1, None, {"title": "Test.svg"})  # type: ignore

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
