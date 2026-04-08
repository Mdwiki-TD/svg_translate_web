"""Unit tests for copy_svg_langs worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

from src.main_app.public_jobs_workers.copy_svg_langs.worker import (
    CopySvgLangsWorker,
    copy_svg_langs_worker_entry,
)


class TestCopySvgLangsWorker:
    def test_get_job_type(self) -> None:
        worker = CopySvgLangsWorker(
            task_id=1,
            args={"title": "Test.svg"},
        )
        assert worker.get_job_type() == "copy_svg_langs"

    def test_get_initial_result_structure(self) -> None:
        worker = CopySvgLangsWorker(
            task_id=1,
            args={"title": "Test.svg"},
        )
        result = worker.get_initial_result()

        assert result["status"] == "pending"
        assert result["started_at"] is not None
        assert result["completed_at"] is None
        assert result["cancelled_at"] is None
        assert result["title"] is None  # title comes from args, not set until processor runs
        assert "stages" in result
        assert "text" in result["stages"]
        assert "titles" in result["stages"]
        assert "translations" in result["stages"]
        assert "download" in result["stages"]
        assert "nested" in result["stages"]
        assert "inject" in result["stages"]
        assert "upload" in result["stages"]

    def test_get_initial_result_stages_have_status(self) -> None:
        worker = CopySvgLangsWorker(
            task_id=1,
            args={"title": "Test.svg"},
        )
        result = worker.get_initial_result()

        for _, stage_data in result["stages"].items():
            assert "status" in stage_data
            assert "message" in stage_data
            assert stage_data["status"] == "Pending"

    def test_worker_init_with_user(self) -> None:
        user = {"username": "testuser", "id": 123}
        worker = CopySvgLangsWorker(
            task_id=1,
            args={"title": "Test.svg"},
            user=user,
        )
        assert worker.user == user

    def test_worker_init_with_cancel_event(self) -> None:
        cancel_event = threading.Event()
        worker = CopySvgLangsWorker(
            task_id=1,
            args={"title": "Test.svg"},
            cancel_event=cancel_event,
        )
        assert worker.cancel_event is cancel_event


class TestCopySvgLangsWorkerEntry:
    def test_worker_entry_missing_title(self) -> None:
        with patch("src.main_app.public_jobs_workers.copy_svg_langs.worker.CopySvgLangsWorker"):
            copy_svg_langs_worker_entry(
                task_id="1",
                args={"title": ""},
                user=None,
            )

    def test_worker_entry_missing_args(self) -> None:
        with patch("src.main_app.public_jobs_workers.copy_svg_langs.worker.CopySvgLangsWorker"):
            copy_svg_langs_worker_entry(
                task_id="1",
                args={"title": "Test.svg"},
                user=None,
            )

    def test_worker_entry_creates_worker(self) -> None:
        with patch("src.main_app.public_jobs_workers.copy_svg_langs.worker.CopySvgLangsWorker") as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            copy_svg_langs_worker_entry(
                task_id="123",
                args={"title": "Test.svg"},
                user={"id": 1},
            )

            MockWorker.assert_called_once_with(
                task_id="123",
                args={"title": "Test.svg"},
                user={"id": 1},
                cancel_event=None,
            )
            mock_instance.run.assert_called_once()

    def test_worker_entry_with_cancel_event(self) -> None:
        cancel_event = threading.Event()
        with patch("src.main_app.public_jobs_workers.copy_svg_langs.worker.CopySvgLangsWorker") as MockWorker:
            mock_instance = MagicMock()
            MockWorker.return_value = mock_instance

            copy_svg_langs_worker_entry(
                task_id="456",
                args={"title": "Another.svg"},
                user=None,
                cancel_event=cancel_event,
            )

            MockWorker.assert_called_once()
            _, kwargs = MockWorker.call_args
            assert kwargs["cancel_event"] is cancel_event
