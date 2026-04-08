"""
Unit tests for fix_nested_jobs processor module.
"""

from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from src.main_app.public_jobs_workers.fix_nested_jobs.job import FixNestedJobsProcessor

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_result(stages=None):
    """Return a minimal result dict mirroring what the real job initialises."""
    default_stages = {
        "download": {"status": None, "message": None},
        "analyze": {"status": None, "message": None},
        "fix": {"status": None, "message": None},
        "verify": {"status": None, "message": None},
        "upload": {"status": None, "message": None},
    }
    if stages:
        default_stages.update(stages)
    return {
        "status": "pending",
        "stages": default_stages,
        "file_result": {},
    }


def _make_processor(
    filename="File:test.svg",
    user=None,
    args=None,
    cancel_event=None,
    result=None,
):
    """Factory for FixNestedJobsProcessor with sensible defaults."""
    if args is None:
        args = {"filename": filename, "upload": True}
    if result is None:
        result = _make_result()
    return FixNestedJobsProcessor(
        task_id=42,
        args=args,
        user=user or {"username": "testuser"},
        result=result,
        result_file="result_42.json",
        cancel_event=cancel_event,
    )


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
        assert proc.session is None


# ---------------------------------------------------------------------------
# _save_progress
# ---------------------------------------------------------------------------


class TestSaveProgress:
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_delegates_to_jobs_service(self, mock_svc):
        proc = _make_processor()
        proc._save_progress()
        mock_svc.save_job_result_by_name.assert_called_once_with(proc.result_file, proc.result)

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_swallows_exceptions(self, mock_svc):
        mock_svc.save_job_result_by_name.side_effect = RuntimeError("disk full")
        proc = _make_processor()
        # Must not raise
        proc._save_progress()


# ---------------------------------------------------------------------------
# _is_cancelled
# ---------------------------------------------------------------------------


class TestIsCancelled:
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_returns_false_when_not_cancelled(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = False
        proc = _make_processor()
        assert proc._is_cancelled() is False

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_cancel_event_set_returns_true(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = False
        event = threading.Event()
        event.set()
        proc = _make_processor(cancel_event=event)
        assert proc._is_cancelled() is True

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_jobs_service_cancelled_returns_true(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = True
        proc = _make_processor()
        assert proc._is_cancelled() is True

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_sets_result_status_to_cancelled(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = True
        proc = _make_processor()
        proc._is_cancelled()
        assert proc.result["status"] == "Cancelled"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_sets_cancelled_at_timestamp(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = True
        proc = _make_processor()
        proc._is_cancelled()
        assert proc.result.get("cancelled_at") is not None

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_does_not_overwrite_existing_cancelled_at(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = True
        proc = _make_processor()
        proc.result["cancelled_at"] = "original"
        proc._is_cancelled()
        assert proc.result["cancelled_at"] == "original"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_updates_stage_status_when_stage_name_given(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = True
        proc = _make_processor()
        proc._is_cancelled("download")
        assert proc.result["stages"]["download"]["status"] == "Cancelled"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_ignores_unknown_stage_name(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = True
        proc = _make_processor()
        # should not raise
        proc._is_cancelled("nonexistent_stage")


# ---------------------------------------------------------------------------
# _update_step
# ---------------------------------------------------------------------------


class TestUpdateStep:
    def test_updates_status_and_message(self):
        proc = _make_processor()
        proc._update_step("download", "success", "all good")
        assert proc.result["stages"]["download"]["status"] == "success"
        assert proc.result["stages"]["download"]["message"] == "all good"


# ---------------------------------------------------------------------------
# Individual step methods (unit-tested in isolation)
# ---------------------------------------------------------------------------


class TestDownloadStep:
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.download_svg_file")
    def test_success_populates_file_result(self, mock_dl, tmp_path):
        svg = tmp_path / "test.svg"
        svg.touch()
        mock_dl.return_value = {"ok": True, "path": svg}
        proc = _make_processor()
        result = proc._download_step()
        assert result is True
        assert proc.result["file_result"]["success"] is True
        assert proc.result["stages"]["download"]["status"] == "success"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.download_svg_file")
    def test_failure_populates_file_result_with_error(self, mock_dl):
        mock_dl.return_value = {"ok": False, "error": "network_error"}
        proc = _make_processor()
        result = proc._download_step()
        assert result is False
        assert proc.result["file_result"]["success"] is False
        assert proc.result["file_result"]["error"] == "network_error"
        assert proc.result["stages"]["download"]["status"] == "Failed"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.download_svg_file")
    def test_failure_defaults_error_when_missing(self, mock_dl):
        mock_dl.return_value = {"ok": False}
        proc = _make_processor()
        proc._download_step()
        assert proc.result["file_result"]["error"] == "download_failed"


class TestAnalyzeStep:
    def _proc_with_download_success(self, path):
        proc = _make_processor()
        proc.result["stages"]["download"]["status"] = "success"
        proc.result["file_result"] = {"path": str(path), "success": True}
        return proc

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.detect_nested_tags")
    def test_skips_when_download_not_success(self, mock_detect):
        proc = _make_processor()
        proc.result["stages"]["download"]["status"] = "Failed"
        proc.result["file_result"] = {}
        result = proc._analyze_step()
        assert result is None
        mock_detect.assert_not_called()

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.detect_nested_tags")
    def test_returns_false_when_file_missing(self, mock_detect, tmp_path):
        proc = self._proc_with_download_success(tmp_path / "missing.svg")
        result = proc._analyze_step()
        assert result is False
        mock_detect.assert_not_called()

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.detect_nested_tags")
    def test_returns_none_when_no_nested_tags(self, mock_detect, tmp_path):
        svg = tmp_path / "a.svg"
        svg.touch()
        mock_detect.return_value = {"count": 0, "tags": []}
        proc = self._proc_with_download_success(svg)
        result = proc._analyze_step()
        assert result is None
        assert proc.result["stages"]["analyze"]["status"] == "skipped"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.detect_nested_tags")
    def test_returns_true_when_nested_tags_found(self, mock_detect, tmp_path):
        svg = tmp_path / "b.svg"
        svg.touch()
        mock_detect.return_value = {"count": 3, "tags": ["g", "g", "svg"]}
        proc = self._proc_with_download_success(svg)
        result = proc._analyze_step()
        assert result is True
        assert proc.result["file_result"]["nested_tags_before"] == 3
        assert proc.result["stages"]["analyze"]["status"] == "success"


class TestFixStep:
    def _proc_after_analyze(self, path):
        proc = _make_processor()
        proc.result["stages"]["analyze"]["status"] = "success"
        proc.result["stages"]["analyze"]["message"] = "found tags"
        proc.result["file_result"] = {"path": str(path)}
        return proc

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.fix_nested_tags")
    def test_skips_when_analyze_not_success(self, mock_fix):
        proc = _make_processor()
        proc.result["stages"]["analyze"]["status"] = "skipped"
        proc.result["stages"]["analyze"]["message"] = "No nested tags found"
        result = proc._fix_step()
        assert result is None
        mock_fix.assert_not_called()

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.fix_nested_tags")
    def test_returns_true_on_success(self, mock_fix, tmp_path):
        mock_fix.return_value = True
        proc = self._proc_after_analyze(tmp_path / "x.svg")
        result = proc._fix_step()
        assert result is True
        assert proc.result["stages"]["fix"]["status"] == "success"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.fix_nested_tags")
    def test_returns_false_on_failure(self, mock_fix, tmp_path):
        mock_fix.return_value = False
        proc = self._proc_after_analyze(tmp_path / "x.svg")
        result = proc._fix_step()
        assert result is False
        assert proc.result["stages"]["fix"]["status"] == "Failed"


class TestVerifyStep:
    def _proc_after_fix(self, path, before_count=5):
        proc = _make_processor()
        proc.result["stages"]["fix"]["status"] = "success"
        proc.result["file_result"] = {"path": str(path), "nested_tags_before": before_count}
        return proc

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.verify_fix")
    def test_skips_when_fix_not_success(self, mock_verify):
        proc = _make_processor()
        proc.result["stages"]["fix"]["status"] = "Failed"
        result = proc._verify_step()
        assert result is None
        mock_verify.assert_not_called()

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.verify_fix")
    def test_returns_true_when_tags_fixed(self, mock_verify, tmp_path):
        mock_verify.return_value = {"after": 0, "fixed": 5}
        proc = self._proc_after_fix(tmp_path / "x.svg", before_count=5)
        result = proc._verify_step()
        assert result is True
        assert proc.result["file_result"]["nested_tags_after"] == 0
        assert proc.result["file_result"]["nested_tags_fixed"] == 5
        assert proc.result["stages"]["verify"]["status"] == "success"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.verify_fix")
    def test_returns_false_when_no_tags_fixed(self, mock_verify, tmp_path):
        mock_verify.return_value = {"after": 5, "fixed": 0}
        proc = self._proc_after_fix(tmp_path / "x.svg", before_count=5)
        result = proc._verify_step()
        assert result is False
        assert proc.result["stages"]["verify"]["status"] == "Failed"


class TestUploadStep:
    def _proc_after_verify(self, tags_fixed=3):
        proc = _make_processor()
        proc.site = MagicMock()
        proc.result["stages"]["verify"]["status"] = "success"
        proc.result["file_result"] = {"path": "/tmp/x.svg", "nested_tags_fixed": tags_fixed}
        return proc

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.upload_fixed_svg")
    def test_skips_when_upload_disabled(self, mock_upload):
        proc = _make_processor(args={"filename": "File:x.svg", "upload": False})
        proc.result["stages"]["verify"]["status"] = "success"
        result = proc._upload_step()
        assert result is None
        mock_upload.assert_not_called()

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.upload_fixed_svg")
    def test_skips_when_no_site(self, mock_upload):
        proc = self._proc_after_verify()
        proc.site = None
        result = proc._upload_step()
        assert result is None
        mock_upload.assert_not_called()

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.upload_fixed_svg")
    def test_skips_when_verify_not_success(self, mock_upload):
        proc = self._proc_after_verify()
        proc.result["stages"]["verify"]["status"] = "Failed"
        result = proc._upload_step()
        assert result is None
        mock_upload.assert_not_called()

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.upload_fixed_svg")
    def test_returns_true_on_success(self, mock_upload):
        mock_upload.return_value = {"ok": True}
        proc = self._proc_after_verify()
        result = proc._upload_step()
        assert result is True
        assert proc.result["stages"]["upload"]["status"] == "success"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.upload_fixed_svg")
    def test_returns_false_on_failure(self, mock_upload):
        mock_upload.return_value = {"ok": False, "error": "permission_denied"}
        proc = self._proc_after_verify()
        result = proc._upload_step()
        assert result is False
        assert proc.result["stages"]["upload"]["status"] == "Failed"
        assert proc.result["stages"]["upload"]["message"] == "permission_denied"


# ---------------------------------------------------------------------------
# _run_stage
# ---------------------------------------------------------------------------


class TestRunStage:
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_returns_true_when_step_returns_true(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = False
        proc = _make_processor()
        assert proc._run_stage("download", lambda: True) is True

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_returns_false_and_sets_failed_when_step_returns_false(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = False
        proc = _make_processor()
        assert proc._run_stage("download", lambda: False) is False
        assert proc.result["status"] == "Failed"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_returns_false_and_sets_skipped_when_step_returns_none(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = False
        proc = _make_processor()
        assert proc._run_stage("download", lambda: None) is False
        assert proc.result["status"] == "skipped"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_handles_exception_and_sets_failed(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = False
        proc = _make_processor()

        def boom():
            raise ValueError("oops")

        assert proc._run_stage("download", boom) is False
        assert proc.result["stages"]["download"]["status"] == "Failed"
        assert "oops" in proc.result["stages"]["download"]["message"]
        assert proc.result["status"] == "Failed"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_returns_false_immediately_when_cancelled(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = True
        step = MagicMock(return_value=True)
        proc = _make_processor()
        assert proc._run_stage("download", step) is False
        step.assert_not_called()

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service")
    def test_sets_stage_status_to_running_before_calling_step(self, mock_svc):
        mock_svc.is_job_cancelled.return_value = False
        statuses = []

        def capture_status():
            statuses.append(proc.result["stages"]["download"]["status"])
            return True

        proc = _make_processor()
        proc._run_stage("download", capture_status)
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
            "jobs_service": patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service"),
            "create_session": patch(
                "src.main_app.public_jobs_workers.fix_nested_jobs.job.create_commons_session",
                return_value=MagicMock(),
            ),
            "get_site": patch(
                "src.main_app.public_jobs_workers.fix_nested_jobs.job.get_user_site",
                return_value=MagicMock(),
            ),
            "download": patch(
                "src.main_app.public_jobs_workers.fix_nested_jobs.job.download_svg_file",
                return_value={"ok": True, "path": svg},
            ),
            "detect": patch(
                "src.main_app.public_jobs_workers.fix_nested_jobs.job.detect_nested_tags",
                return_value={"count": 2, "tags": ["g", "g"]},
            ),
            "fix": patch(
                "src.main_app.public_jobs_workers.fix_nested_jobs.job.fix_nested_tags",
                return_value=True,
            ),
            "verify": patch(
                "src.main_app.public_jobs_workers.fix_nested_jobs.job.verify_fix",
                return_value={"after": 0, "fixed": 2},
            ),
            "upload": patch(
                "src.main_app.public_jobs_workers.fix_nested_jobs.job.upload_fixed_svg",
                return_value={"ok": True},
            ),
        }
        return patches

    def test_happy_path_returns_completed(self, tmp_path):
        patchers = self._patch_all(tmp_path)
        mocks = {k: v.start() for k, v in patchers.items()}
        mocks["jobs_service"].is_job_cancelled.return_value = False

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
        mocks["jobs_service"].is_job_cancelled.return_value = False

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
        mocks["jobs_service"].is_job_cancelled.return_value = False
        mocks["download"].return_value = {"ok": False, "error": "timeout"}

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

        call_count = [0]

        def cancel_on_third(*_, **kwargs):
            call_count[0] += 1
            return call_count[0] >= 3

        mocks["jobs_service"].is_job_cancelled.side_effect = cancel_on_third

        try:
            proc = _make_processor()
            result = proc.run()
            assert result["status"] == "Cancelled"
            mocks["upload"].assert_not_called()
        finally:
            for p in patchers.values():
                p.stop()

    def test_all_stages_keys_present_in_result(self, tmp_path):
        patchers = self._patch_all(tmp_path)
        mocks = {k: v.start() for k, v in patchers.items()}
        mocks["jobs_service"].is_job_cancelled.return_value = False

        try:
            proc = _make_processor()
            result = proc.run()
            for stage in ("download", "analyze", "fix", "verify", "upload"):
                assert stage in result["stages"]
        finally:
            for p in patchers.values():
                p.stop()
