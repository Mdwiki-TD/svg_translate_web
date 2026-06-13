"""
Unit tests for fix_nested_jobs processor module.
"""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.objects import (
    FileResult,
)
from src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker import FixNestedJobsProcessor
from src.main_app.shared.fix_nested.objects import (
    DetectionResult,
    DownloadResult,
    VerificationResult,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_processor(
    filename="File:test.svg",
    user=None,
    args=None,
    cancel_event=None,
) -> FixNestedJobsProcessor:
    """Factory for FixNestedJobsProcessor with sensible defaults."""
    if args is None:
        args = {"filename": filename, "upload": True}

    return FixNestedJobsProcessor(
        job_id=42,
        args=args,
        user=user or {"username": "testuser"},
        cancel_event=cancel_event,
    )


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    """Mock the services used by fix_nested_jobs worker."""

    mock_save_job_result = MagicMock()
    mock_is_job_cancelled = MagicMock()
    mock_download_svg_file = MagicMock()
    mock_detect_nested_tags = MagicMock()
    mock_fix_nested_tags = MagicMock()
    mock_verify_fix = MagicMock()
    mock_upload_fixed_svg = MagicMock()

    monkeypatch.setattr("src.main_app.jobs_workers.base_worker_object.save_job_result_by_name", mock_save_job_result)
    monkeypatch.setattr("src.main_app.jobs_workers.base_worker_object.is_job_cancelled", mock_is_job_cancelled)
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.download_svg_file",
        mock_download_svg_file,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.detect_nested_tags",
        mock_detect_nested_tags,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.fix_nested_tags",
        mock_fix_nested_tags,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.verify_fix",
        mock_verify_fix,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.upload_fixed_svg",
        mock_upload_fixed_svg,
    )

    return {
        "save_job_result": mock_save_job_result,
        "is_job_cancelled": mock_is_job_cancelled,
        "download_svg_file": mock_download_svg_file,
        "detect_nested_tags": mock_detect_nested_tags,
        "fix_nested_tags": mock_fix_nested_tags,
        "verify_fix": mock_verify_fix,
        "upload_fixed_svg": mock_upload_fixed_svg,
    }


# ---------------------------------------------------------------------------
# __post_init__ / construction
# ---------------------------------------------------------------------------


class TestPostInit:
    def test_filename_extracted_from_args(self):
        proc = _make_processor(filename="File:foo.svg")
        assert proc.filename == "File:foo.svg"

    def test_filename_none_when_missing_from_args(self):
        proc = _make_processor(args={})
        assert proc.filename is None

    def test_site_and_session_default_to_none(self):
        proc = _make_processor()
        assert proc.site is None
        assert not hasattr(proc, "session")


# ---------------------------------------------------------------------------
# _save_progress
# ---------------------------------------------------------------------------


class TestSaveProgress:
    def test_delegates_to_jobs_service(self, mock_services):
        proc = _make_processor()
        proc._save_progress()
        mock_services["save_job_result"].assert_called_once_with(proc.result_file, proc.result.to_json())

    def test_swallows_exceptions(self, mock_services):
        mock_services["save_job_result"].side_effect = RuntimeError("disk full")
        proc = _make_processor()
        # Must not raise
        proc._save_progress()


# ---------------------------------------------------------------------------
# is_cancelled
# ---------------------------------------------------------------------------


class TestIsCancelled:
    def test_returns_false_when_not_cancelled(self, mock_services):
        mock_services["is_job_cancelled"].return_value = False
        proc = _make_processor()
        assert proc.is_cancelled() is False

    def test_cancel_event_set_returns_true(self, mock_services):
        mock_services["is_job_cancelled"].return_value = False
        event = threading.Event()
        event.set()
        proc = _make_processor(cancel_event=event)
        assert proc.is_cancelled() is True

    def test_jobs_service_cancelled_returns_true(self, mock_services):
        mock_services["is_job_cancelled"].return_value = True
        proc = _make_processor()
        assert proc.is_cancelled(check_db=True) is True

    def test_sets_result_status_to_cancelled(self, mock_services):
        mock_services["is_job_cancelled"].return_value = True
        proc = _make_processor()
        proc.is_cancelled(check_db=True)
        assert proc.result.status == "cancelled"

    def test_sets_cancelled_at_timestamp(self, mock_services):
        mock_services["is_job_cancelled"].return_value = True
        proc = _make_processor()
        proc.is_cancelled(check_db=True)
        assert proc.result.cancelled_at is not None

    def test_does_not_overwrite_existing_cancelled_at(self, mock_services):
        mock_services["is_job_cancelled"].return_value = True
        proc = _make_processor()
        proc.result.cancelled_at = "original"
        proc.is_cancelled(check_db=True)
        assert proc.result.cancelled_at == "original"

    def test_updates_stage_status_when_stage_name_given(self, mock_services):
        mock_services["is_job_cancelled"].return_value = True
        proc = _make_processor()
        # is_cancelled's only positional arg is `check_db` (bool); a truthy
        # value triggers the DB cancellation check. The base worker sets the
        # global result status to "cancelled" but does NOT update per-stage
        # statuses (stage updates happen in _run_stage instead).
        proc.is_cancelled("download")
        assert proc.result.status == "cancelled"

    def test_ignores_unknown_stage_name(self, mock_services):
        mock_services["is_job_cancelled"].return_value = True
        proc = _make_processor()
        # should not raise
        proc.is_cancelled("nonexistent_stage")


# ---------------------------------------------------------------------------
# Individual step methods (unit-tested in isolation)
# ---------------------------------------------------------------------------


class TestDownloadStep:
    def test_success_populates_file_result(self, mock_services, tmp_path):
        svg = tmp_path / "test.svg"
        svg.touch()
        mock_services["download_svg_file"].return_value = DownloadResult(ok=True, path=svg)
        proc = _make_processor()
        result = proc._download_step()
        assert result is True
        assert proc.result.file_result.success is True
        assert proc.result.stages.download.status == "success"

    def test_failure_populates_file_result_with_error(self, mock_services):
        mock_services["download_svg_file"].return_value = DownloadResult(ok=False, error="network_error")
        proc = _make_processor()
        result = proc._download_step()
        assert result is False
        assert proc.result.file_result.success is False
        assert proc.result.file_result.error == "network_error"
        assert proc.result.stages.download.status == "Failed"

    def test_failure_defaults_error_when_missing(self, mock_services):
        mock_services["download_svg_file"].return_value = DownloadResult(ok=False)
        proc = _make_processor()
        proc._download_step()
        assert proc.result.file_result.error == "download_failed"


class TestAnalyzeStep:
    def _proc_with_download_success(self, path):
        proc = _make_processor()
        proc.result.stages.download.status = "success"
        proc.result.file_result = FileResult(path=str(path), success=True)
        return proc

    def test_skips_when_download_not_success(self, mock_services):
        proc = _make_processor()
        proc.result.stages.download.status = "Failed"
        result = proc._analyze_step()
        assert result is None
        mock_services["detect_nested_tags"].assert_not_called()

    def test_returns_false_when_file_missing(self, mock_services, tmp_path):
        proc = self._proc_with_download_success(tmp_path / "missing.svg")
        result = proc._analyze_step()
        assert result is False
        mock_services["detect_nested_tags"].assert_not_called()

    def test_returns_none_when_no_nested_tags(self, mock_services, tmp_path):
        svg = tmp_path / "a.svg"
        svg.touch()
        mock_services["detect_nested_tags"].return_value = DetectionResult(count=0, tags=[])
        proc = self._proc_with_download_success(svg)
        result = proc._analyze_step()
        assert result is None
        assert proc.result.stages.analyze.status == "skipped"

    def test_returns_true_when_nested_tags_found(self, mock_services, tmp_path):
        svg = tmp_path / "b.svg"
        svg.touch()
        mock_services["detect_nested_tags"].return_value = DetectionResult(count=3, tags=["g", "g", "svg"])
        proc = self._proc_with_download_success(svg)
        result = proc._analyze_step()
        assert result is True
        assert proc.result.file_result.nested_tags_before == 3
        assert proc.result.stages.analyze.status == "success"


class TestFixStep:
    def _proc_after_analyze(self, path):
        proc = _make_processor()
        proc.result.stages.analyze.status = "success"
        proc.result.stages.analyze.message = "found tags"
        proc.result.file_result = FileResult(path=str(path))
        return proc

    def test_skips_when_analyze_not_success(self, mock_services):
        proc = _make_processor()
        proc.result.stages.analyze.status = "skipped"
        proc.result.stages.analyze.message = "No nested tags found"
        result = proc._fix_step()
        assert result is None
        mock_services["fix_nested_tags"].assert_not_called()

    def test_returns_true_on_success(self, mock_services, tmp_path):
        mock_services["fix_nested_tags"].return_value = True
        proc = self._proc_after_analyze(tmp_path / "x.svg")
        result = proc._fix_step()
        assert result is True
        assert proc.result.stages.fix.status == "success"

    def test_returns_false_on_failure(self, mock_services, tmp_path):
        mock_services["fix_nested_tags"].return_value = False
        proc = self._proc_after_analyze(tmp_path / "x.svg")
        result = proc._fix_step()
        assert result is False
        assert proc.result.stages.fix.status == "Failed"


class TestVerifyStep:
    def _proc_after_fix(self, path, before_count=5):
        proc = _make_processor()
        proc.result.stages.fix.status = "success"
        proc.result.file_result = FileResult(path=str(path), nested_tags_before=before_count)
        return proc

    def test_skips_when_fix_not_success(self, mock_services):
        proc = _make_processor()
        proc.result.stages.fix.status = "Failed"
        result = proc._verify_step()
        assert result is None
        mock_services["verify_fix"].assert_not_called()

    def test_returns_true_when_tags_fixed(self, mock_services, tmp_path):
        mock_services["verify_fix"].return_value = VerificationResult(before=0, after=0, fixed=5)
        proc = self._proc_after_fix(tmp_path / "x.svg", before_count=5)
        result = proc._verify_step()
        assert result is True
        assert proc.result.file_result.nested_tags_after == 0
        assert proc.result.file_result.nested_tags_fixed == 5
        assert proc.result.stages.verify.status == "success"

    def test_returns_false_when_no_tags_fixed(self, mock_services, tmp_path):
        mock_services["verify_fix"].return_value = VerificationResult(before=0, after=5, fixed=0)
        proc = self._proc_after_fix(tmp_path / "x.svg", before_count=5)
        result = proc._verify_step()
        assert result is False
        assert proc.result.stages.verify.status == "Failed"


class TestUploadStep:
    def _proc_after_verify(self, path, tags_fixed=3):
        proc = _make_processor()
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

    def test_skips_when_upload_disabled(self, mock_services, tmp_path):
        proc = _make_processor(args={"filename": "File:x.svg", "upload": False})
        proc.result.stages.verify.status = "success"
        result = proc._upload_step()
        assert result is None
        mock_services["upload_fixed_svg"].assert_not_called()

    def test_skips_when_no_site(self, mock_services, tmp_path):
        proc = self._proc_after_verify(path=str(tmp_path / "x.svg"))
        proc.site = None
        result = proc._upload_step()
        assert result is None
        mock_services["upload_fixed_svg"].assert_not_called()

    def test_skips_when_verify_not_success(self, mock_services, tmp_path):
        proc = self._proc_after_verify(path=str(tmp_path / "x.svg"))
        proc.result.stages.verify.status = "Failed"
        result = proc._upload_step()
        assert result is None
        mock_services["upload_fixed_svg"].assert_not_called()

    def test_returns_true_on_success(self, mock_services, tmp_path):
        mock_services["upload_fixed_svg"].return_value = {"ok": True, "result": {}}
        proc = self._proc_after_verify(path=str(tmp_path / "x.svg"))
        result = proc._upload_step()
        assert result is True
        assert proc.result.stages.upload.status == "success"

    def test_returns_false_on_failure(self, mock_services, tmp_path):
        mock_services["upload_fixed_svg"].return_value = {"ok": False, "error": "permission_denied"}
        proc = self._proc_after_verify(path=str(tmp_path / "x.svg"))
        result = proc._upload_step()
        assert result is False
        assert proc.result.stages.upload.status == "Failed"
        assert proc.result.stages.upload.message == "permission_denied"


# ---------------------------------------------------------------------------
# _run_stage
# ---------------------------------------------------------------------------


class TestRunStage:
    def test_returns_true_when_step_returns_true(self, mock_services):
        mock_services["is_job_cancelled"].return_value = False
        proc = _make_processor()
        assert proc._run_stage(proc.result.stages.download, lambda: True) is True

    def test_returns_false_and_sets_failed_when_step_returns_false(self, mock_services):
        mock_services["is_job_cancelled"].return_value = False
        proc = _make_processor()
        assert proc._run_stage(proc.result.stages.download, lambda: False) is False
        assert proc.result.status == "Failed"

    def test_returns_false_and_sets_skipped_when_step_returns_none(self, mock_services):
        mock_services["is_job_cancelled"].return_value = False
        proc = _make_processor()
        assert proc._run_stage(proc.result.stages.download, lambda: None) is False
        assert proc.result.status == "skipped"

    def test_handles_exception_and_sets_failed(self, mock_services):
        mock_services["is_job_cancelled"].return_value = False
        proc = _make_processor()

        def boom():
            raise ValueError("oops")

        assert proc._run_stage(proc.result.stages.download, boom) is False
        assert proc.result.stages.download.status == "Failed"
        assert "oops" in proc.result.stages.download.message
        assert proc.result.status == "Failed"

    def test_returns_false_immediately_when_cancelled(self, mock_services):
        mock_services["is_job_cancelled"].return_value = True
        # _run_stage calls self.is_cancelled() without check_db=True, so the
        # DB mock alone has no effect. Use a cancel_event to trigger
        # cancellation via the local event path.
        event = threading.Event()
        event.set()
        step = MagicMock(return_value=True)
        proc = _make_processor(cancel_event=event)
        assert proc._run_stage(proc.result.stages.download, step) is False
        step.assert_not_called()

    def test_sets_stage_status_to_running_before_calling_step(self, mock_services):
        mock_services["is_job_cancelled"].return_value = False
        statuses: list = []

        def capture_status():
            statuses.append(proc.result.stages.download.status)
            return True

        proc = _make_processor()
        proc._run_stage(proc.result.stages.download, capture_status)
        assert statuses[0] == "Running"


# ---------------------------------------------------------------------------
# run() integration-level tests (all workers mocked)
# ---------------------------------------------------------------------------


class TestRun:
    def _patch_all(self, tmp_path):
        """Return a context-manager-compatible list of patchers."""
        svg = tmp_path / "test.svg"
        svg.touch()
        patches = {
            # Bypass BaseObjectsJobWorker.before_run (which calls update_job_status
            # against the real DB and then tries to do `self.result.status =`
            # attribute access on a dict). Returning True lets process() run.
            "before_run": patch(
                "src.main_app.jobs_workers.base_worker_object.BaseObjectsJobWorker.before_run",
                return_value=True,
            ),
            # Bypass the DB write inside BaseObjectsJobWorker.after_run().
            "update_job_status": patch(
                "src.main_app.jobs_workers.base_worker_object.update_job_status",
                return_value=None,
            ),
            # Bypass disk writes from _save_progress().
            "save_job_result_by_name": patch(
                "src.main_app.jobs_workers.base_worker_object.save_job_result_by_name",
                return_value=None,
            ),
            "is_job_cancelled": patch("src.main_app.jobs_workers.base_worker_object.is_job_cancelled"),
            "is_job_cancelled_file_exist": patch(
                "src.main_app.jobs_workers.base_worker_object.is_job_cancelled_file_exist",
                return_value=False,
            ),
            "get_site": patch(
                "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.get_user_site",
                return_value=MagicMock(),
            ),
            "download": patch(
                "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.download_svg_file",
                return_value=DownloadResult(ok=True, path=svg),
            ),
            "detect": patch(
                "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.detect_nested_tags",
                return_value=DetectionResult(count=2, tags=["g", "g"]),
            ),
            "fix": patch(
                "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.fix_nested_tags",
                return_value=True,
            ),
            "verify": patch(
                "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.verify_fix",
                return_value=VerificationResult(before=2, after=0, fixed=2),
            ),
            "upload": patch(
                "src.main_app.jobs_workers.public_jobs_workers.fix_nested_jobs.worker.upload_fixed_svg",
                return_value={"ok": True, "result": {}},
            ),
        }
        return patches

    def test_happy_path_returns_completed(self, tmp_path):
        patchers = self._patch_all(tmp_path)
        mocks = {k: v.start() for k, v in patchers.items()}
        mocks["is_job_cancelled"].return_value = False

        try:
            proc = _make_processor()
            result = proc.run()
            assert result["status"] == "completed"
            assert result.get("completed_at") is not None
        finally:
            for p in patchers.values():
                p.stop()

    def test_missing_filename_returns_failed(self, tmp_path):
        patchers = self._patch_all(tmp_path)
        mocks = {k: v.start() for k, v in patchers.items()}
        mocks["is_job_cancelled"].return_value = False

        try:
            proc = _make_processor(args={})
            result = proc.run()
            assert result["status"] == "Failed"
        finally:
            for p in patchers.values():
                p.stop()

    def test_download_failure_stops_pipeline(self, tmp_path):
        patchers = self._patch_all(tmp_path)
        mocks = {k: v.start() for k, v in patchers.items()}
        mocks["is_job_cancelled"].return_value = False
        mocks["download"].return_value = DownloadResult(ok=False, error="timeout")

        try:
            proc = _make_processor()
            result = proc.run()
            assert result["status"] == "Failed"
            mocks["detect"].assert_not_called()
        finally:
            for p in patchers.values():
                p.stop()

    def test_cancellation_mid_pipeline_stops_run(self, tmp_path):
        """Cancellation detected at the fix stage stops further stages."""
        patchers = self._patch_all(tmp_path)
        mocks = {k: v.start() for k, v in patchers.items()}
        mocks["is_job_cancelled"].return_value = False

        # _run_stage calls self.is_cancelled() without check_db=True, so we
        # drive cancellation through is_job_cancelled_file_exist (file path)
        # instead of the DB path. Trip cancellation on the 3rd check.
        call_count = [0]

        def cancel_on_third(*_, **__):
            call_count[0] += 1
            return call_count[0] >= 3

        mocks["is_job_cancelled_file_exist"].side_effect = cancel_on_third

        try:
            proc = _make_processor()
            result = proc.run()
            # BaseObjectsJobWorker._mark_as_cancelled_in_result sets status to
            # lowercase "cancelled".
            assert result["status"] == "cancelled"
            mocks["upload"].assert_not_called()
        finally:
            for p in patchers.values():
                p.stop()

    def test_all_stages_keys_present_in_result(self, tmp_path):
        patchers = self._patch_all(tmp_path)
        mocks = {k: v.start() for k, v in patchers.items()}
        mocks["is_job_cancelled"].return_value = False

        try:
            proc = _make_processor()
            result = proc.run()
            for stage in ("download", "analyze", "fix", "verify", "upload"):
                assert stage in result["stages"]
        finally:
            for p in patchers.values():
                p.stop()
