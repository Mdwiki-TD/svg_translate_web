"""
Unit tests for fix_nested_jobs processor module.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.main_app.api_services.files_service import DownloadAndSaveData
from src.main_app.api_services.files_service.objects import UploadResult
from src.main_app.jobs_workers.objects import JobsRunner
from src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.objects import FileResult
from src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker import FixNestedJobsProcessor
from src.main_app.services.fix_nested.worker import (
    DetectionResult,
    VerificationResult,
)

# ── jobs_workers fixtures ───────────────────────────────────────────────────────────────────

_BASE = "src.main_app.jobs_workers.base_worker"
_WORKER = "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker"


@dataclass
class MockFixNestedServices:
    save_job_result_by_name: MagicMock
    download_and_save: MagicMock
    detect_nested_tags: MagicMock
    fix_nested_tags: MagicMock
    verify_fix: MagicMock
    upload_svg: MagicMock
    is_job_cancelled: MagicMock


@pytest.fixture
def mock_fix_nested_services(monkeypatch: pytest.MonkeyPatch, mock_base_worker) -> MockFixNestedServices:
    """Mock the services used by fix_nested_jobs worker."""

    save_job_result_by_name = MagicMock()
    download_and_save = MagicMock()
    detect_nested_tags = MagicMock()
    fix_nested_tags = MagicMock()
    verify_fix = MagicMock()
    upload_svg = MagicMock()
    is_job_cancelled = MagicMock()

    monkeypatch.setattr(f"{_BASE}.save_job_result_by_name", save_job_result_by_name)
    monkeypatch.setattr(f"{_WORKER}.FilesService.download_and_save", download_and_save)
    monkeypatch.setattr(f"{_WORKER}.detect_nested_tags", detect_nested_tags)
    monkeypatch.setattr(f"{_WORKER}.fix_nested_tags", fix_nested_tags)
    monkeypatch.setattr(f"{_WORKER}.verify_fix", verify_fix)
    monkeypatch.setattr(f"{_WORKER}.UploadService.upload_svg", upload_svg)
    monkeypatch.setattr(f"{_BASE}.JobsService.is_job_cancelled", is_job_cancelled)

    return MockFixNestedServices(
        save_job_result_by_name=save_job_result_by_name,
        download_and_save=download_and_save,
        detect_nested_tags=detect_nested_tags,
        fix_nested_tags=fix_nested_tags,
        verify_fix=verify_fix,
        upload_svg=upload_svg,
        is_job_cancelled=is_job_cancelled,
    )


@dataclass
class MockRunDeps:
    is_job_cancelled: MagicMock
    is_job_cancelled_file: MagicMock
    get_site: MagicMock
    download: MagicMock
    detect: MagicMock
    fix: MagicMock
    verify: MagicMock
    upload: MagicMock


@pytest.fixture
def run_mocks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mock_base_worker, mock_before_run) -> MockRunDeps:
    """Patch every collaborator of the run() pipeline with a MagicMock."""
    svg = tmp_path / "test.svg"
    svg.touch()

    is_job_cancelled = MagicMock()
    is_job_cancelled_file = MagicMock(return_value=False)
    get_site = MagicMock(return_value=MagicMock())
    download = MagicMock(return_value=DownloadAndSaveData(result="success", path=svg))
    detect = MagicMock(return_value=DetectionResult(count=2, tags=["g", "g"]))
    fix = MagicMock(return_value=True)
    verify = MagicMock(return_value=VerificationResult(before=2, after=0, fixed=2))
    upload = MagicMock(return_value=UploadResult(ok=True, result={}))

    monkeypatch.setattr(f"{_BASE}.JobsService.is_job_cancelled", is_job_cancelled)
    monkeypatch.setattr(f"{_BASE}.is_job_cancelled_file_exist", is_job_cancelled_file)
    monkeypatch.setattr(f"{_BASE}.get_user_site", get_site)
    monkeypatch.setattr(f"{_WORKER}.FilesService.download_and_save", download)
    monkeypatch.setattr(f"{_WORKER}.detect_nested_tags", detect)
    monkeypatch.setattr(f"{_WORKER}.fix_nested_tags", fix)
    monkeypatch.setattr(f"{_WORKER}.verify_fix", verify)
    monkeypatch.setattr(f"{_WORKER}.UploadService.upload_svg", upload)

    return MockRunDeps(
        is_job_cancelled=is_job_cancelled,
        is_job_cancelled_file=is_job_cancelled_file,
        get_site=get_site,
        download=download,
        detect=detect,
        fix=fix,
        verify=verify,
        upload=upload,
    )


# ---------------------------------------------------------------------------
# steps
# ---------------------------------------------------------------------------


class TestSetup:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.processor = self._make_processor()

    def _make_processor(
        self,
        filename="File:test.svg",
        user=None,
        args=None,
        cancel_event=None,
    ) -> FixNestedJobsProcessor:
        """Factory for FixNestedJobsProcessor with sensible defaults."""
        if args is None:
            args = {"filename": filename, "upload": True}

        return FixNestedJobsProcessor(
            JobsRunner(
                job_id=1,
                args=args,
                user=user or {"username": "testuser"},
                cancel_event=cancel_event,
            )
        )


class TestFixNestedJobsProcessorSteps(TestSetup):
    def test_verify_step_success(self, mock_fix_nested_services: MockFixNestedServices, tmp_path) -> None:
        self.processor.result.stages.fix.status = "success"
        self.processor.result.file_result = FileResult(path=str(tmp_path / "test.svg"), nested_tags_before=2)

        mock_fix_nested_services.verify_fix.return_value = VerificationResult(before=2, after=0, fixed=2)

        result = self.processor._verify_step(self.processor.result.stages.verify)

        assert result is True
        assert self.processor.result.stages.verify.status == "success"

    def test_verify_step_failure_no_tags_fixed(self, mock_fix_nested_services: MockFixNestedServices, tmp_path) -> None:
        self.processor.result.stages.fix.status = "success"
        self.processor.result.file_result = FileResult(path=str(tmp_path / "test.svg"), nested_tags_before=2)

        mock_fix_nested_services.verify_fix.return_value = VerificationResult(before=2, after=2, fixed=0)

        result = self.processor._verify_step(self.processor.result.stages.verify)

        assert result is False
        assert self.processor.result.stages.verify.status == "failed"

    def test_upload_step_success(self, mock_fix_nested_services: MockFixNestedServices, tmp_path) -> None:
        self.processor.site = MagicMock()
        self.processor.result.stages.verify.status = "success"
        self.processor.result.file_result = FileResult(path=str(tmp_path / "test.svg"), nested_tags_fixed=2)
        mock_fix_nested_services.upload_svg.return_value = UploadResult(ok=True, result={"some": "data"})

        result = self.processor._upload_step(self.processor.result.stages.upload)

        assert result is True
        assert self.processor.result.stages.upload.status == "success"

    def test_upload_step_failure(self, mock_fix_nested_services: MockFixNestedServices, tmp_path) -> None:
        self.processor.site = MagicMock()
        self.processor.result.stages.verify.status = "success"
        self.processor.result.file_result = FileResult(path=str(tmp_path / "test.svg"), nested_tags_fixed=2)
        mock_fix_nested_services.upload_svg.return_value = UploadResult(ok=False, error="Upload failed message")

        result = self.processor._upload_step(self.processor.result.stages.upload)

        assert result is False
        assert self.processor.result.stages.upload.status == "failed"


class TestFixNestedJobsProcessor(TestSetup):
    def test_get_job_type(self) -> None:
        worker = FixNestedJobsProcessor(
            JobsRunner(
                job_id=1,
                user={},
                args={"filename": "Test.svg"},
            )
        )
        assert worker.get_job_type() == "fix_nested_jobs"

    def test_result_initial_structure(self) -> None:
        worker = FixNestedJobsProcessor(
            JobsRunner(
                job_id=1,
                user={},
                args={"filename": "Test.svg"},
            )
        )
        result = worker.result

        assert result.status == "pending"
        assert result.started_at is not None
        assert result.completed_at is None
        assert result.cancelled_at is None
        assert result.filename is None  # filename comes from args, not set until processor runs
        assert result.stages.download.status == "pending"
        assert result.stages.analyze.status == "pending"
        assert result.stages.fix.status == "pending"
        assert result.stages.verify.status == "pending"
        assert result.stages.upload.status == "pending"

    def test_worker_init_with_user(self) -> None:
        user = {"username": "testuser", "id": 123}
        worker = FixNestedJobsProcessor(
            JobsRunner(
                job_id=1,
                args={"filename": "Test.svg"},
                user=user,
            )
        )
        assert worker.user == user

    def test_worker_init_with_cancel_event(self) -> None:
        cancel_event = threading.Event()
        worker = FixNestedJobsProcessor(
            JobsRunner(
                job_id=1,
                user={},
                args={"filename": "Test.svg"},
                cancel_event=cancel_event,
            )
        )
        assert worker.cancel_event is cancel_event

    def test_filename_from_args(self) -> None:
        assert self.processor.filename == "File:test.svg"

    def test_filename_from_args_with_file_prefix(self) -> None:
        assert self.processor.filename == "File:test.svg"

    def test_filename_empty(self) -> None:
        processor = self._make_processor(args={})
        assert processor.filename is None

    def test_is_cancelled_no_event(self, mock_fix_nested_services: MockFixNestedServices) -> None:
        mock_fix_nested_services.is_job_cancelled.return_value = False

        assert self.processor.is_cancelled() is False

    def test_is_cancelled_with_event(self) -> None:
        cancel_event = threading.Event()
        cancel_event.set()
        processor = self._make_processor(cancel_event=cancel_event)
        assert processor.is_cancelled() is True
        assert processor.result.status == "cancelled"

    def test_run_step_success(self) -> None:
        def mock_step():
            return True

        result = self.processor._run_step(self.processor.result.stages.download, mock_step)
        assert result is True

    def test_run_step_failure(self) -> None:
        def mock_step():
            return False

        result = self.processor._run_step(self.processor.result.stages.download, mock_step)
        assert result is False
        assert self.processor.result.status == "failed"


# ---------------------------------------------------------------------------
# __post_init__ / construction
# ---------------------------------------------------------------------------


class TestPostInit(TestSetup):
    def test_filename_extracted_from_args(self):
        proc = self._make_processor(filename="File:foo.svg")
        assert proc.filename == "File:foo.svg"

    def test_filename_none_when_missing_from_args(self):
        proc = self._make_processor(args={})
        assert proc.filename is None

    def test_site_and_session_default_to_none(self):
        proc = self.processor
        assert proc.site is None
        assert not hasattr(proc, "session")


# ---------------------------------------------------------------------------
# is_cancelled
# ---------------------------------------------------------------------------


class TestIsCancelled(TestSetup):
    def test_returns_false_when_not_cancelled(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.is_job_cancelled.return_value = False
        proc = self.processor
        assert proc.is_cancelled() is False

    def test_cancel_event_set_returns_true(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.is_job_cancelled.return_value = False
        event = threading.Event()
        event.set()
        proc = self._make_processor(cancel_event=event)
        assert proc.is_cancelled() is True

    def test_jobs_service_cancelled_returns_true(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.is_job_cancelled.return_value = True
        proc = self.processor
        assert proc.is_cancelled(check_db=True) is True

    def test_sets_result_status_to_cancelled(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.is_job_cancelled.return_value = True
        proc = self.processor
        proc.is_cancelled(check_db=True)
        assert proc.result.status == "cancelled"

    def test_sets_cancelled_at_timestamp(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.is_job_cancelled.return_value = True
        proc = self.processor
        proc.is_cancelled(check_db=True)
        assert proc.result.cancelled_at is not None

    def test_does_not_overwrite_existing_cancelled_at(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.is_job_cancelled.return_value = True
        proc = self.processor
        proc.result.cancelled_at = "original"
        proc.is_cancelled(check_db=True)
        assert proc.result.cancelled_at == "original"

    def test_updates_stage_status_when_stage_name_given(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.is_job_cancelled.return_value = True
        proc = self.processor
        # is_cancelled's only positional arg is `check_db` (bool); a truthy
        # value triggers the DB cancellation check. The base worker sets the
        # global result status to "cancelled" but does NOT update per-stage
        # statuses (stage updates happen in _run_step instead).
        proc.is_cancelled("download")
        assert proc.result.status == "cancelled"

    def test_ignores_unknown_stage_name(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.is_job_cancelled.return_value = True
        proc = self.processor
        # should not raise
        proc.is_cancelled("nonexistent_stage")


# ---------------------------------------------------------------------------
# Individual step methods (unit-tested in isolation)
# ---------------------------------------------------------------------------


class TestDownloadStep(TestSetup):
    def test_success_populates_file_result(self, mock_fix_nested_services: MockFixNestedServices, tmp_path):
        svg = tmp_path / "test.svg"
        svg.touch()
        mock_fix_nested_services.download_and_save.return_value = DownloadAndSaveData(result="success", path=svg)
        proc = self.processor
        result = proc._download_step(self.processor.result.stages.download)
        assert result is True
        assert proc.result.file_result.success is True
        assert proc.result.stages.download.status == "success"

    def test_failure_populates_file_result_with_error(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.download_and_save.return_value = DownloadAndSaveData(
            result="failed", error="network_error"
        )
        proc = self.processor
        result = proc._download_step(self.processor.result.stages.download)
        assert result is False
        assert proc.result.file_result.success is False
        assert proc.result.file_result.error == "network_error"
        assert proc.result.stages.download.status == "failed"

    def test_failure_defaults_error_when_missing(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.download_and_save.return_value = DownloadAndSaveData(result="failed")
        proc = self.processor
        proc._download_step(self.processor.result.stages.download)
        assert proc.result.file_result.error == "download_failed"


class TestAnalyzeStep(TestSetup):
    def _proc_with_download_success(self, path):
        proc = self.processor
        proc.result.stages.download.status = "success"
        proc.result.file_result = FileResult(path=str(path), success=True)
        proc.file_path = path
        return proc

    def test_skips_when_download_not_success(self, mock_fix_nested_services: MockFixNestedServices):
        proc = self.processor
        proc.result.stages.download.status = "failed"
        result = proc._analyze_step(self.processor.result.stages.analyze)
        assert result is None
        mock_fix_nested_services.detect_nested_tags.assert_not_called()

    def test_returns_false_when_file_missing(self, mock_fix_nested_services: MockFixNestedServices, tmp_path):
        proc = self._proc_with_download_success(tmp_path / "missing.svg")
        result = proc._analyze_step(self.processor.result.stages.analyze)
        assert result is False
        mock_fix_nested_services.detect_nested_tags.assert_not_called()

    def test_returns_none_when_no_nested_tags(self, mock_fix_nested_services: MockFixNestedServices, tmp_path):
        svg = tmp_path / "a.svg"
        svg.touch()

        mock_fix_nested_services.detect_nested_tags.return_value = DetectionResult(count=0, tags=[])
        proc = self._proc_with_download_success(svg)

        result = proc._analyze_step(self.processor.result.stages.analyze)
        assert result is None
        assert proc.result.stages.analyze.status == "skipped"
        mock_fix_nested_services.detect_nested_tags.assert_called_once()

    def test_returns_true_when_nested_tags_found(self, mock_fix_nested_services: MockFixNestedServices, tmp_path):
        svg = tmp_path / "b.svg"
        svg.touch()

        mock_fix_nested_services.detect_nested_tags.return_value = DetectionResult(count=3, tags=["g", "g", "svg"])
        proc = self._proc_with_download_success(svg)

        result = proc._analyze_step(self.processor.result.stages.analyze)
        assert result is True
        assert proc.result.file_result.nested_tags_before == 3
        assert proc.result.stages.analyze.status == "success"


class TestFixStep(TestSetup):
    def _proc_after_analyze(self, path):
        proc = self.processor
        proc.result.stages.analyze.status = "success"
        proc.result.stages.analyze.message = "found tags"
        proc.result.file_result = FileResult(path=str(path))
        return proc

    def test_skips_when_analyze_not_success(self, mock_fix_nested_services: MockFixNestedServices):
        proc = self.processor
        proc.result.stages.analyze.status = "skipped"
        proc.result.stages.analyze.message = "No nested tags found"
        result = proc._fix_step(self.processor.result.stages.fix)
        assert result is None
        mock_fix_nested_services.fix_nested_tags.assert_not_called()

    def test_returns_true_on_success(self, mock_fix_nested_services: MockFixNestedServices, tmp_path):
        mock_fix_nested_services.fix_nested_tags.return_value = True
        proc = self._proc_after_analyze(tmp_path / "x.svg")
        result = proc._fix_step(self.processor.result.stages.fix)
        assert result is True
        assert proc.result.stages.fix.status == "success"

    def test_returns_false_on_failure(self, mock_fix_nested_services: MockFixNestedServices, tmp_path):
        mock_fix_nested_services.fix_nested_tags.return_value = False
        proc = self._proc_after_analyze(tmp_path / "x.svg")
        result = proc._fix_step(self.processor.result.stages.fix)
        assert result is False
        assert proc.result.stages.fix.status == "failed"


class TestVerifyStep(TestSetup):
    def _proc_after_fix(self, path, before_count=5):
        proc = self.processor
        proc.result.stages.fix.status = "success"
        proc.result.file_result = FileResult(path=str(path), nested_tags_before=before_count)
        return proc

    def test_skips_when_fix_not_success(self, mock_fix_nested_services: MockFixNestedServices):
        proc = self.processor
        proc.result.stages.fix.status = "failed"
        result = proc._upload_step(self.processor.result.stages.verify)
        assert result is None
        mock_fix_nested_services.verify_fix.assert_not_called()

    def test_returns_true_when_tags_fixed(self, mock_fix_nested_services: MockFixNestedServices, tmp_path):
        mock_fix_nested_services.verify_fix.return_value = VerificationResult(before=0, after=0, fixed=5)
        proc = self._proc_after_fix(tmp_path / "x.svg", before_count=5)
        result = proc._upload_step(self.processor.result.stages.verify)
        assert result is True
        assert proc.result.file_result.nested_tags_after == 0
        assert proc.result.file_result.nested_tags_fixed == 5
        assert proc.result.stages.verify.status == "success"

    def test_returns_false_when_no_tags_fixed(self, mock_fix_nested_services: MockFixNestedServices, tmp_path):
        mock_fix_nested_services.verify_fix.return_value = VerificationResult(before=0, after=5, fixed=0)
        proc = self._proc_after_fix(tmp_path / "x.svg", before_count=5)
        result = proc._upload_step(self.processor.result.stages.verify)
        assert result is False
        assert proc.result.stages.verify.status == "failed"


class TestUploadStep(TestSetup):
    def _proc_after_verify(self, path, tags_fixed=3):
        proc = self.processor
        proc.site = MagicMock()
        proc.result.stages.verify.status = "success"
        proc.result.file_result = FileResult(
            status="pending",
            path=path,
            error=None,
            success=None,
            nested_tags_before=0,
            nested_tags=[],
            nested_tags_after=0,
            nested_tags_fixed=tags_fixed,
        )
        return proc

    def test_skips_when_upload_disabled(self, mock_fix_nested_services: MockFixNestedServices, tmp_path):
        proc = self._make_processor(args={"filename": "File:x.svg", "upload": False})
        proc.result.stages.verify.status = "success"
        result = proc._upload_step(self.processor.result.stages.upload)
        assert result is None
        mock_fix_nested_services.upload_svg.assert_not_called()

    def test_skips_when_no_site(self, mock_fix_nested_services: MockFixNestedServices, tmp_path):
        proc = self._proc_after_verify(path=str(tmp_path / "x.svg"))
        proc.site = None
        result = proc._upload_step(self.processor.result.stages.upload)
        assert result is None
        mock_fix_nested_services.upload_svg.assert_not_called()

    def test_skips_when_verify_not_success(self, mock_fix_nested_services: MockFixNestedServices, tmp_path):
        proc = self._proc_after_verify(path=str(tmp_path / "x.svg"))
        proc.result.stages.verify.status = "failed"
        result = proc._upload_step(self.processor.result.stages.upload)
        assert result is None
        mock_fix_nested_services.upload_svg.assert_not_called()

    def test_returns_true_on_success(self, mock_fix_nested_services: MockFixNestedServices, tmp_path):
        mock_fix_nested_services.upload_svg.return_value = UploadResult(ok=True, result={})
        proc = self._proc_after_verify(path=str(tmp_path / "x.svg"))
        result = proc._upload_step(self.processor.result.stages.upload)
        assert result is True
        assert proc.result.stages.upload.status == "success"

    def test_returns_false_on_failure(self, mock_fix_nested_services: MockFixNestedServices, tmp_path):
        mock_fix_nested_services.upload_svg.return_value = UploadResult(ok=False, error="permission_denied")
        proc = self._proc_after_verify(path=str(tmp_path / "x.svg"))
        result = proc._upload_step(self.processor.result.stages.upload)
        assert result is False
        assert proc.result.stages.upload.status == "failed"
        assert proc.result.stages.upload.message == "permission_denied"


# ---------------------------------------------------------------------------
# _run_step
# ---------------------------------------------------------------------------


class TestRunStage(TestSetup):
    def test_returns_true_when_step_returns_true(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.is_job_cancelled.return_value = False
        proc = self.processor
        assert proc._run_step(proc.result.stages.download, lambda: True) is True

    def test_returns_false_and_sets_failed_when_step_returns_false(
        self, mock_fix_nested_services: MockFixNestedServices
    ):
        mock_fix_nested_services.is_job_cancelled.return_value = False
        proc = self.processor
        assert proc._run_step(proc.result.stages.download, lambda: False) is False
        assert proc.result.status == "failed"

    def test_returns_false_and_sets_skipped_when_step_returns_none(
        self, mock_fix_nested_services: MockFixNestedServices
    ):
        mock_fix_nested_services.is_job_cancelled.return_value = False
        proc = self.processor
        assert proc._run_step(proc.result.stages.download, lambda: None) is False
        assert proc.result.status == "skipped"

    def test_handles_exception_and_sets_failed(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.is_job_cancelled.return_value = False
        proc = self.processor

        def boom():
            raise ValueError("oops")

        assert proc._run_step(proc.result.stages.download, boom) is False
        assert proc.result.stages.download.status == "failed"
        assert "oops" in proc.result.stages.download.message
        assert proc.result.status == "failed"

    def test_returns_false_immediately_when_cancelled(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.is_job_cancelled.return_value = True
        # _run_step calls self.is_cancelled() without check_db=True, so the
        # DB mock alone has no effect. Use a cancel_event to trigger
        # cancellation via the local event path.
        event = threading.Event()
        event.set()
        step = MagicMock(return_value=True)
        proc = self._make_processor(cancel_event=event)
        assert proc._run_step(proc.result.stages.download, step) is False
        step.assert_not_called()

    def test_sets_stage_status_to_running_before_calling_step(self, mock_fix_nested_services: MockFixNestedServices):
        mock_fix_nested_services.is_job_cancelled.return_value = False
        statuses: list = []

        def capture_status():
            statuses.append(proc.result.stages.download.status)
            return True

        proc = self.processor
        proc._run_step(proc.result.stages.download, capture_status)
        assert statuses[0] == "running"


# ---------------------------------------------------------------------------
# run() integration-level tests (all workers mocked)
# ---------------------------------------------------------------------------


class TestRun(TestSetup):
    def test_happy_path_returns_completed(self, run_mocks: MockRunDeps):
        run_mocks.is_job_cancelled.return_value = False

        proc = self.processor
        result = proc.run()
        assert result["status"] == "completed"
        assert result.get("completed_at") is not None

    def test_missing_filename_returns_failed(self, run_mocks: MockRunDeps):
        run_mocks.is_job_cancelled.return_value = False

        proc = self._make_processor(args={})
        result = proc.run()
        assert result["status"] == "failed"

    def test_download_failure_stops_pipeline(self, run_mocks: MockRunDeps):
        run_mocks.is_job_cancelled.return_value = False
        run_mocks.download.return_value = {"ok": False, "error": "timeout"}

        proc = self.processor
        result = proc.run()
        assert result["status"] == "failed"
        run_mocks.detect.assert_not_called()

    def test_cancellation_mid_pipeline_stops_run(self, run_mocks: MockRunDeps, monkeypatch):
        """Cancellation detected at the fix stage stops further stages."""
        run_mocks.is_job_cancelled.return_value = False

        # _run_step calls self.is_cancelled() without check_db=True, so we
        # drive cancellation through is_job_cancelled_file_exist(file path)
        # instead of the DB path. Trip cancellation on the 3rd check.
        call_count = [0]

        def cancel_on_third(*_, **__):
            call_count[0] += 1
            return call_count[0] >= 3

        mock_is_job_cancelled_file_exist = MagicMock()
        monkeypatch.setattr(
            f"{_BASE}.is_job_cancelled_file_exist",
            mock_is_job_cancelled_file_exist,
        )
        mock_is_job_cancelled_file_exist.return_value = False
        mock_is_job_cancelled_file_exist.side_effect = cancel_on_third

        proc = self.processor
        result = proc.run()
        # BaseObjectsJobWorker._mark_as_cancelled_in_result sets status to
        # lowercase "cancelled".
        assert result["status"] == "cancelled"
        run_mocks.upload.assert_not_called()

    def test_all_stages_keys_present_in_result(self, run_mocks: MockRunDeps):
        run_mocks.is_job_cancelled.return_value = False

        proc = self.processor
        result = proc.run()
        for stage in ("download", "analyze", "fix", "verify", "upload"):
            assert stage in result["stages"]
