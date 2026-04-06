"""Unit tests for copy_svg_langs service."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.public_jobs_workers.copy_svg_langs.service import (
    get_cancel_event,
    start_copy_svg_langs_job,
)


class TestStartCopySvgLangsJob:
    def test_start_copy_svg_langs_job_creates_job(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_job = MagicMock()
        mock_job.id = 123

        mock_create_job = MagicMock(return_value=mock_job)
        monkeypatch.setattr(
            "src.main_app.public_jobs_workers.copy_svg_langs.service.jobs_service.create_job", mock_create_job
        )

        mock_register = MagicMock()
        monkeypatch.setattr(
            "src.main_app.public_jobs_workers.copy_svg_langs.service._register_cancel_event",
            mock_register,
        )

        mock_thread = MagicMock()
        monkeypatch.setattr(threading, "Thread", mock_thread)

        job_id = start_copy_svg_langs_job(
            title="Test.svg",
            args={"main": "Test.svg"},
            user={"username": "testuser"},
        )

        assert job_id == 123
        mock_create_job.assert_called_once_with("copy_svg_langs", "testuser")
        mock_register.assert_called_once()
        mock_thread.assert_called_once()

        call_kwargs = mock_thread.call_args.kwargs
        assert call_kwargs["daemon"] is True

    def test_start_copy_svg_langs_job_without_user(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_job = MagicMock()
        mock_job.id = 456

        mock_create_job = MagicMock(return_value=mock_job)
        monkeypatch.setattr(
            "src.main_app.public_jobs_workers.copy_svg_langs.service.jobs_service.create_job", mock_create_job
        )

        mock_register = MagicMock()
        monkeypatch.setattr(
            "src.main_app.public_jobs_workers.copy_svg_langs.service._register_cancel_event",
            mock_register,
        )

        mock_thread = MagicMock()
        monkeypatch.setattr(threading, "Thread", mock_thread)

        job_id = start_copy_svg_langs_job(
            title="Another.svg",
            args={"main": "Another.svg"},
            user=None,
        )

        assert job_id == 456
        mock_create_job.assert_called_once_with("copy_svg_langs", None)

    def test_start_copy_svg_langs_job_starts_thread(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_job = MagicMock()
        mock_job.id = 789

        mock_create_job = MagicMock(return_value=mock_job)
        monkeypatch.setattr(
            "src.main_app.public_jobs_workers.copy_svg_langs.service.jobs_service.create_job", mock_create_job
        )

        mock_register = MagicMock()
        monkeypatch.setattr(
            "src.main_app.public_jobs_workers.copy_svg_langs.service._register_cancel_event",
            mock_register,
        )

        mock_thread_instance = MagicMock()
        mock_thread_class = MagicMock(return_value=mock_thread_instance)
        monkeypatch.setattr(threading, "Thread", mock_thread_class)

        job_id = start_copy_svg_langs_job(
            title="ThreadTest.svg",
            args={"mode": "copy"},
            user={"username": "threaduser"},
        )

        mock_thread_class.assert_called_once()
        mock_thread_instance.start.assert_called_once()


class TestGetCancelEvent:
    def test_get_cancel_event_returns_event(self, monkeypatch: pytest.MonkeyPatch) -> None:
        expected_event = threading.Event()
        monkeypatch.setattr(
            "src.main_app.public_jobs_workers.copy_svg_langs.service.get_jobs_cancel_event",
            MagicMock(return_value=expected_event),
        )

        result = get_cancel_event(123)

        assert result is expected_event

    def test_get_cancel_event_with_string_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        expected_event = threading.Event()
        monkeypatch.setattr(
            "src.main_app.public_jobs_workers.copy_svg_langs.service.get_jobs_cancel_event",
            MagicMock(return_value=expected_event),
        )

        result = get_cancel_event("456")

        assert result is expected_event

    def test_get_cancel_event_returns_none_for_unknown_job(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.main_app.public_jobs_workers.copy_svg_langs.service.get_jobs_cancel_event",
            MagicMock(return_value=None),
        )

        result = get_cancel_event(999)

        assert result is None
