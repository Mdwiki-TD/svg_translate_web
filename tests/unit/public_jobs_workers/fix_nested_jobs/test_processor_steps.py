"""Unit tests for fix_nested_jobs processor steps."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

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
                "stages": {"verify": {"message": "", "status": ""}, "fix": {"status": ""}},
            },
            result_file="test.json",
        )
        mock_verify_fix.return_value = {"after": 0, "fixed": 2}

        result = processor._verify_step()

        assert result["success"] is True
        assert "2 tags fixed" in result["message"]
        assert processor.result["stages"]["verify"]["status"] == "success"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.verify_fix")
    def test_verify_step_failure_no_tags_fixed(self, mock_verify_fix) -> None:
        processor = FixNestedJobsProcessor(
            task_id=1,
            args={"filename": "Test.svg"},
            user=None,
            result={
                "file_result": {
                    "path": "/tmp/test.svg",
                    "nested_tags_before": 2,
                },
                "stages": {"verify": {"message": "", "status": ""}, "fix": {"status": ""}},
            },
            result_file="test.json",
        )
        mock_verify_fix.return_value = {"after": 2, "fixed": 0}

        result = processor._verify_step()

        # This should fail after the fix
        assert result["success"] is False
        assert "fix failed" in result["error"]
        assert processor.result["stages"]["verify"]["status"] == "skipped"

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
                "stages": {"verify": {"message": "", "status": ""}, "upload": {"message": "", "status": ""}},
            },
            result_file="test.json",
        )
        mock_upload_fixed_svg.return_value = {"ok": True, "result": {"some": "data"}}

        result = processor._upload_step()

        assert result["success"] is True
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
                "stages": {"verify": {"message": "", "status": ""}, "upload": {"message": "", "status": ""}},
            },
            result_file="test.json",
        )
        mock_upload_fixed_svg.return_value = {"ok": False, "error": "Upload failed message"}

        result = processor._upload_step()

        # This should fail after the fix
        assert result["success"] is False
        assert result["error"] == "Skipped (not fixed)"
        assert processor.result["stages"]["upload"]["status"] == "skipped"
