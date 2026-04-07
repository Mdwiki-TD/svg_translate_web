"""Unit tests for fix_nested_jobs processor module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

from src.main_app.public_jobs_workers.fix_nested_jobs.job import FixNestedJobsProcessor


class TestFixNestedJobsProcessor:
    def test_parse_filenames_single_string(self) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            title="Test.svg",
            args={"filename": "Test.svg"},
            user=None,
            result={},
            result_file="test.json",
        )
        filenames = processor._parse_filenames()
        assert filenames == ["Test.svg"]

    def test_parse_filenames_list(self) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            title="Test.svg",
            args={"filenames": ["File1.svg", "File2.svg"]},
            user=None,
            result={},
            result_file="test.json",
        )
        filenames = processor._parse_filenames()
        assert filenames == ["File1.svg", "File2.svg"]

    def test_parse_filenames_comma_separated(self) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            title="Test.svg",
            args={"filenames": "File1.svg, File2.svg, File3.svg"},
            user=None,
            result={},
            result_file="test.json",
        )
        filenames = processor._parse_filenames()
        assert filenames == ["File1.svg", "File2.svg", "File3.svg"]

    def test_parse_filenames_removes_file_prefix(self) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            title="Test.svg",
            args={"filename": "File:Test.svg"},
            user=None,
            result={},
            result_file="test.json",
        )
        filenames = processor._parse_filenames()
        assert filenames == ["Test.svg"]

    def test_parse_filenames_empty(self) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            title="Test.svg",
            args={},
            user=None,
            result={},
            result_file="test.json",
        )
        filenames = processor._parse_filenames()
        assert filenames == []

    def test_is_cancelled_no_event(self) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            title="Test.svg",
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
            title="Test.svg",
            args={"filename": "Test.svg"},
            user=None,
            result={"status": "running"},
            result_file="test.json",
            cancel_event=cancel_event,
        )
        assert processor._is_cancelled() is True
        assert processor.result["status"] == "cancelled"

    def test_run_stage_success(self) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            title="Test.svg",
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

    def test_run_stage_failure(self) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            title="Test.svg",
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
