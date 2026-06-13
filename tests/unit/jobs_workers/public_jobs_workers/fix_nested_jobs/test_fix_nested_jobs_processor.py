"""Unit tests for fix_nested_jobs processor module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.objects import FileResult
from src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker import FixNestedJobsProcessor

from src.main_app.shared.fix_nested.objects import UploadResult, VerificationResult


def _make_processor(filename="File:test.svg", user=None, args=None, cancel_event=None):
    """Factory for FixNestedJobsProcessor with sensible defaults."""
    if args is None:
        args = {"filename": filename}
    return FixNestedJobsProcessor(
        job_id=1,
        args=args,
        user=user,
        cancel_event=cancel_event,
    )


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    """Mock the services used by fix_nested_jobs worker."""

    mock_verify_fix = MagicMock()
    mock_upload_fixed_svg = MagicMock()
    mock_is_job_cancelled = MagicMock()

    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.verify_fix",
        mock_verify_fix,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.upload_fixed_svg",
        mock_upload_fixed_svg,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker_object.is_job_cancelled",
        mock_is_job_cancelled,
    )

    return {
        "verify_fix": mock_verify_fix,
        "upload_fixed_svg": mock_upload_fixed_svg,
        "is_job_cancelled": mock_is_job_cancelled,
    }


class TestFixNestedJobsProcessorSteps:
    def test_verify_step_success(self, mock_services) -> None:
        processor = _make_processor()
        processor.result.stages.fix.status = "success"
        processor.result.file_result = FileResult(path="/tmp/test.svg", nested_tags_before=2)
        mock_services["verify_fix"].return_value = VerificationResult(before=2, after=0, fixed=2)

        result = processor._verify_step()

        assert result is True
        assert processor.result.stages.verify.status == "success"

    def test_verify_step_failure_no_tags_fixed(self, mock_services) -> None:
        processor = _make_processor()
        processor.result.stages.fix.status = "success"
        processor.result.file_result = FileResult(path="/tmp/test.svg", nested_tags_before=2)
        mock_services["verify_fix"].return_value = VerificationResult(before=2, after=2, fixed=0)

        result = processor._verify_step()

        assert result is False
        assert processor.result.stages.verify.status == "Failed"

    def test_upload_step_success(self, mock_services) -> None:
        processor = _make_processor()
        processor.site = MagicMock()
        processor.result.stages.verify.status = "success"
        processor.result.file_result = FileResult(path="/tmp/test.svg", nested_tags_fixed=2)
        mock_services["upload_fixed_svg"].return_value = UploadResult(ok=True, result={"some": "data"})

        result = processor._upload_step()

        assert result is True
        assert processor.result.stages.upload.status == "success"

    def test_upload_step_failure(self, mock_services) -> None:
        processor = _make_processor()
        processor.site = MagicMock()
        processor.result.stages.verify.status = "success"
        processor.result.file_result = FileResult(path="/tmp/test.svg", nested_tags_fixed=2)
        mock_services["upload_fixed_svg"].return_value = UploadResult(ok=False, error="Upload failed message")

        result = processor._upload_step()

        assert result is False
        assert processor.result.stages.upload.status == "Failed"


class TestFixNestedJobsProcessor:
    def test_filename_from_args(self) -> None:
        processor = _make_processor()
        assert processor.filename == "File:test.svg"

    def test_filename_from_args_with_file_prefix(self) -> None:
        processor = _make_processor()
        assert processor.filename == "File:test.svg"

    def test_filename_empty(self) -> None:
        processor = _make_processor(args={})
        assert processor.filename is None

    def test_is_cancelled_no_event(self, mock_services) -> None:
        mock_services["is_job_cancelled"].return_value = False
        processor = _make_processor()
        assert processor.is_cancelled() is False

    def test_is_cancelled_with_event(self) -> None:
        cancel_event = threading.Event()
        cancel_event.set()
        processor = _make_processor(cancel_event=cancel_event)
        assert processor.is_cancelled() is True
        assert processor.result.status == "cancelled"

    def test_run_stage_success(self, mock_jobs_service) -> None:
        processor = _make_processor()

        def mock_step():
            return True

        result = processor._run_stage("download", mock_step)
        assert result is True

    def test_run_stage_failure(self, mock_jobs_service) -> None:
        processor = _make_processor()

        def mock_step():
            return False

        result = processor._run_stage("download", mock_step)
        assert result is False
        assert processor.result.status == "Failed"
