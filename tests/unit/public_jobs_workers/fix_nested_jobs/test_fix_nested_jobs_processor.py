"""Unit tests for fix_nested_jobs processor module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

from src.main_app.public_jobs_workers.fix_nested_jobs.job import FixNestedJobsProcessor


class TestFixNestedJobsProcessorSteps:
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.verify_fix")
    def test_verify_step_success(self, mock_verify_fix) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            args={"filename": "Test.svg"},
            user=None,
            result={
                "file_result": {
                    "path": "/tmp/test.svg",
                    "nested_tags_before": 2,
                },
                "stages": {"verify": {"message": "", "status": ""}, "fix": {"status": "success"}},
            },
            result_file="test.json",
        )
        mock_verify_fix.return_value = {"after": 0, "fixed": 2}

        result = processor._verify_step()

        assert result is True
        assert processor.result["stages"]["verify"]["status"] == "success"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.verify_fix")
    def test_verify_step_failure_no_tags_fixed(self, mock_verify_fix) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            args={"filename": "Test.svg"},
            user=None,
            result={
                "stages": {"verify": {"message": "", "status": ""}, "fix": {"status": "success"}},
                "file_result": {"path": "/tmp/test.svg", "nested_tags_before": 2},
            },
            result_file="test.json",
        )
        mock_verify_fix.return_value = {"after": 2, "fixed": 0}

        result = processor._verify_step()

        assert result is False
        assert processor.result["stages"]["verify"]["status"] == "Failed"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.upload_fixed_svg")
    def test_upload_step_success(self, mock_upload_fixed_svg) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            args={"filename": "Test.svg"},
            user=None,
            result={
                "file_result": {
                    "path": "/tmp/test.svg",
                    "nested_tags_fixed": 2,
                },
                "stages": {"verify": {"message": "", "status": "success"}, "upload": {"message": "", "status": ""}},
            },
            result_file="test.json",
        )
        processor.site = MagicMock()
        mock_upload_fixed_svg.return_value = {"ok": True, "result": {"some": "data"}}

        result = processor._upload_step()

        assert result is True
        assert processor.result["stages"]["upload"]["status"] == "success"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.upload_fixed_svg")
    def test_upload_step_failure(self, mock_upload_fixed_svg) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            args={"filename": "Test.svg"},
            user=None,
            result={
                "file_result": {
                    "path": "/tmp/test.svg",
                    "nested_tags_fixed": 2,
                },
                "stages": {"verify": {"message": "", "status": "success"}, "upload": {"message": "", "status": ""}},
            },
            result_file="test.json",
        )
        processor.site = MagicMock()
        mock_upload_fixed_svg.return_value = {"ok": False, "error": "Upload failed message"}

        result = processor._upload_step()

        assert result is False
        assert processor.result["stages"]["upload"]["status"] == "Failed"


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
        assert processor.result["status"] == "Cancelled"

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
            return True

        result = processor._run_stage("download", mock_step)
        assert result is True

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
            return False

        result = processor._run_stage("download", mock_step)
        assert result is False
        assert processor.result["status"] == "Failed"
