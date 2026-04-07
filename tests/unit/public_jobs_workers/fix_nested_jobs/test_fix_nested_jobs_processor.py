"""Unit tests for fix_nested_jobs processor module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.public_jobs_workers.fix_nested_jobs.job import FixNestedJobsProcessor


class TestFixNestedJobsProcessor:
    def test_filename_from_args(self) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            args={"filename": "Test.svg"},
            user=None,
            result={},
            result_file="test.json",
        )
        assert processor.filename == "Test.svg"

    def test_filename_from_args_with_file_prefix(self) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            args={"filename": "File:Test.svg"},
            user=None,
            result={},
            result_file="test.json",
        )
        # The processor just gets the value as-is from args
        assert processor.filename == "File:Test.svg"

    def test_filename_empty(self) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            args={},
            user=None,
            result={},
            result_file="test.json",
        )
        assert processor.filename is None

    def test_is_cancelled_no_event(self) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            args={"filename": "Test.svg"},
            user=None,
            result={"status": "running"},
            result_file="test.json",
        )
        with patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service") as mock_jobs:
            mock_jobs.is_job_cancelled.return_value = False
            assert processor._is_cancelled() is False

    def test_is_cancelled_with_event(self) -> None:
        cancel_event = threading.Event()
        cancel_event.set()
        processor = FixNestedJobsProcessor(
            task_id=1,
            args={"filename": "Test.svg"},
            user=None,
            result={"status": "running"},
            result_file="test.json",
            cancel_event=cancel_event,
        )
        assert processor._is_cancelled() is True
        assert processor.result["status"] == "cancelled"

    def test_run_stage_success(self, mock_jobs_service) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            args={"filename": "Test.svg"},
            user=None,
            result={
                "status": "running",
                "stages": {
                    "download": {"status": "Pending", "message": ""},
                },
            },
            result_file="test.json",
        )

        def mock_step():
            return {"success": True, "message": "Done"}

        result = processor._run_stage("download", mock_step)
        assert result is True
        assert processor.result["stages"]["download"]["status"] == "Completed"

    def test_run_stage_failure(self, mock_jobs_service) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            args={"filename": "Test.svg"},
            user=None,
            result={
                "status": "running",
                "stages": {
                    "download": {"status": "Pending", "message": ""},
                },
            },
            result_file="test.json",
        )

        def mock_step():
            return {"success": False, "error": "Failed"}

        result = processor._run_stage("download", mock_step)
        assert result is False
        assert processor.result["stages"]["download"]["status"] == "Failed"
        assert processor.result["status"] == "failed"
