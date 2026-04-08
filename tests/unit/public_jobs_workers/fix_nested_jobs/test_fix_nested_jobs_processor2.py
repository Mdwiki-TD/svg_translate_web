"""
Unit tests for fix_nested_jobs processor module.
"""

from __future__ import annotations

import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.main_app.public_jobs_workers.fix_nested_jobs.job import FixNestedJobsProcessor


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_result(stages=None):
    """Return a minimal result dict that mirrors what the real caller provides."""
    default_stages = {
        "download": {"status": "", "message": ""},
        "analyze": {"status": "", "message": ""},
        "fix": {"status": "", "message": ""},
        "verify": {"status": "", "message": ""},
        "upload": {"status": "", "message": ""},
    }
    return {
        "status": "pending",
        "stages": stages or default_stages,
        "file_result": {},
    }


def _make_processor(
    filename="File:test.svg",
    upload=True,
    user=None,
    cancel_event=None,
    result=None,
):
    return FixNestedJobsProcessor(
        task_id=42,
        args={"filename": filename, "upload": upload},
        user=user or {"username": "testuser"},
        result=result or _make_result(),
        result_file="result.json",
        cancel_event=cancel_event,
    )


# ---------------------------------------------------------------------------
# __post_init__
# ---------------------------------------------------------------------------

class TestPostInit:
    def test_filename_extracted_from_args(self):
        proc = _make_processor(filename="File:foo.svg")
        assert proc.filename == "File:foo.svg"

    def test_filename_none_when_missing(self):
        proc = FixNestedJobsProcessor(
            task_id=1,
            args={},
            user={},
            result=_make_result(),
            result_file="r.json",
        )
        assert proc.filename is None


# ---------------------------------------------------------------------------
# _save_progress
# ---------------------------------------------------------------------------

class TestSaveProgress:
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.save_job_result_by_name")
    def test_calls_service(self, mock_save):
        proc = _make_processor()
        proc._save_progress()
        mock_save.assert_called_once_with("result.json", proc.result)

    @patch(
        "src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.save_job_result_by_name",
        side_effect=RuntimeError("disk full"),
    )
    def test_swallows_exception(self, _mock_save):
        proc = _make_processor()
        proc._save_progress()  # must not raise


# ---------------------------------------------------------------------------
# _is_cancelled
# ---------------------------------------------------------------------------

class TestIsCancelled:
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.is_job_cancelled", return_value=False)
    def test_not_cancelled(self, _mock):
        proc = _make_processor()
        assert proc._is_cancelled() is False

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.is_job_cancelled", return_value=True)
    def test_cancelled_via_service(self, _mock):
        proc = _make_processor()
        assert proc._is_cancelled() is True
        assert proc.result["status"] == "cancelled"

    def test_cancelled_via_event(self):
        event = threading.Event()
        event.set()
        proc = _make_processor(cancel_event=event)
        with patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.is_job_cancelled", return_value=False):
            assert proc._is_cancelled() is True
            assert proc.result["status"] == "cancelled"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.is_job_cancelled", return_value=True)
    def test_cancelled_sets_stage_status(self, _mock):
        proc = _make_processor()
        proc._is_cancelled(stage_name="download")
        assert proc.result["stages"]["download"]["status"] == "Cancelled"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.is_job_cancelled", return_value=True)
    def test_cancelled_records_timestamp_once(self, _mock):
        proc = _make_processor()
        proc._is_cancelled()
        first_ts = proc.result["cancelled_at"]
        proc._is_cancelled()
        assert proc.result["cancelled_at"] == first_ts  # not overwritten


# ---------------------------------------------------------------------------
# _update_step
# ---------------------------------------------------------------------------

class TestUpdateStep:
    def test_sets_status_and_message(self):
        proc = _make_processor()
        proc._update_step("download", "success", "all good")
        assert proc.result["stages"]["download"]["status"] == "success"
        assert proc.result["stages"]["download"]["message"] == "all good"


# ---------------------------------------------------------------------------
# _download_step
# ---------------------------------------------------------------------------

class TestDownloadStep:
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.download_svg_file")
    def test_success(self, mock_dl):
        mock_dl.return_value = {"ok": True, "path": Path("/tmp/test.svg")}
        proc = _make_processor()
        result = proc._download_step()
        assert result["success"] is True
        assert proc.result["stages"]["download"]["status"] == "success"
        assert proc.result["file_result"]["path"] == "/tmp/test.svg"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.download_svg_file")
    def test_failure(self, mock_dl):
        mock_dl.return_value = {"ok": False, "error": "http_error"}
        proc = _make_processor()
        result = proc._download_step()
        assert result["success"] is False
        assert proc.result["stages"]["download"]["status"] == "Failed"
        assert proc.result["file_result"]["error"] == "http_error"


# ---------------------------------------------------------------------------
# _analyze_step
# ---------------------------------------------------------------------------

class TestAnalyzeStep:
    def _proc_with_download_success(self, path: str):
        proc = _make_processor()
        proc.result["stages"]["download"]["status"] = "success"
        proc.result["file_result"] = {"path": path, "success": True}
        return proc

    def test_returns_false_when_download_not_success(self):
        proc = _make_processor()
        proc.result["stages"]["download"]["status"] = "Failed"
        assert proc._analyze_step() is False

    def test_file_not_found(self, tmp_path):
        proc = self._proc_with_download_success(str(tmp_path / "missing.svg"))
        result = proc._analyze_step()
        assert result["success"] is False
        assert proc.result["stages"]["analyze"]["status"] == "Failed"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.detect_nested_tags")
    def test_no_nested_tags(self, mock_detect, tmp_path):
        svg = tmp_path / "test.svg"
        svg.write_text("<svg/>")
        mock_detect.return_value = {"count": 0, "tags": []}
        proc = self._proc_with_download_success(str(svg))
        result = proc._analyze_step()
        assert result["success"] is None
        assert proc.result["stages"]["analyze"]["status"] == "skipped"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.detect_nested_tags")
    def test_nested_tags_found(self, mock_detect, tmp_path):
        svg = tmp_path / "test.svg"
        svg.write_text("<svg/>")
        mock_detect.return_value = {"count": 3, "tags": ["<g>", "<g>", "<g>"]}
        proc = self._proc_with_download_success(str(svg))
        result = proc._analyze_step()
        assert result["success"] is True
        assert proc.result["file_result"]["nested_tags_before"] == 3
        assert proc.result["stages"]["analyze"]["status"] == "success"


# ---------------------------------------------------------------------------
# _fix_step
# ---------------------------------------------------------------------------

class TestFixStep:
    def test_skipped_when_analyze_not_success(self):
        proc = _make_processor()
        proc.result["stages"]["analyze"]["status"] = "skipped"
        proc.result["stages"]["analyze"]["message"] = "No nested tags found"
        proc.result["file_result"] = {"path": "/tmp/x.svg"}
        result = proc._fix_step()
        assert result["success"] is None
        assert proc.result["stages"]["fix"]["status"] == "skipped"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.fix_nested_tags", return_value=True)
    def test_success(self, _mock, tmp_path):
        svg = tmp_path / "test.svg"
        svg.write_text("<svg/>")
        proc = _make_processor()
        proc.result["stages"]["analyze"]["status"] = "success"
        proc.result["file_result"] = {"path": str(svg)}
        result = proc._fix_step()
        assert result["success"] is True
        assert proc.result["stages"]["fix"]["status"] == "success"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.fix_nested_tags", return_value=False)
    def test_failure(self, _mock, tmp_path):
        svg = tmp_path / "test.svg"
        svg.write_text("<svg/>")
        proc = _make_processor()
        proc.result["stages"]["analyze"]["status"] = "success"
        proc.result["file_result"] = {"path": str(svg)}
        result = proc._fix_step()
        assert result["success"] is False
        assert proc.result["stages"]["fix"]["status"] == "Failed"


# ---------------------------------------------------------------------------
# _verify_step
# ---------------------------------------------------------------------------

class TestVerifyStep:
    def test_skipped_when_fix_not_success(self):
        proc = _make_processor()
        proc.result["stages"]["fix"]["status"] = "Failed"
        proc.result["file_result"] = {"path": "/tmp/x.svg", "nested_tags_before": 2}
        result = proc._verify_step()
        assert result["success"] is None

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.verify_fix")
    def test_success(self, mock_verify, tmp_path):
        svg = tmp_path / "test.svg"
        svg.write_text("<svg/>")
        mock_verify.return_value = {"after": 0, "fixed": 3}
        proc = _make_processor()
        proc.result["stages"]["fix"]["status"] = "success"
        proc.result["file_result"] = {"path": str(svg), "nested_tags_before": 3}
        result = proc._verify_step()
        assert result["success"] is True
        assert proc.result["file_result"]["nested_tags_fixed"] == 3
        assert proc.result["stages"]["verify"]["status"] == "success"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.verify_fix")
    def test_no_tags_fixed(self, mock_verify, tmp_path):
        svg = tmp_path / "test.svg"
        svg.write_text("<svg/>")
        mock_verify.return_value = {"after": 3, "fixed": 0}
        proc = _make_processor()
        proc.result["stages"]["fix"]["status"] = "success"
        proc.result["file_result"] = {"path": str(svg), "nested_tags_before": 3}
        result = proc._verify_step()
        assert result["success"] is False
        assert proc.result["stages"]["verify"]["status"] == "Failed"


# ---------------------------------------------------------------------------
# _upload_step
# ---------------------------------------------------------------------------

class TestUploadStep:
    def test_skipped_when_verify_not_success(self):
        proc = _make_processor()
        proc.result["stages"]["verify"]["status"] = "Failed"
        proc.result["file_result"] = {"path": "/tmp/x.svg", "nested_tags_fixed": 0}
        result = proc._upload_step()
        assert result["success"] is None
        assert proc.result["stages"]["upload"]["status"] == "skipped"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.upload_fixed_svg")
    def test_success(self, mock_upload, tmp_path):
        svg = tmp_path / "test.svg"
        svg.write_text("<svg/>")
        mock_upload.return_value = {"ok": True}
        proc = _make_processor()
        proc.result["stages"]["verify"]["status"] = "success"
        proc.result["file_result"] = {"path": str(svg), "nested_tags_fixed": 2}
        result = proc._upload_step()
        assert result["success"] is True
        assert proc.result["stages"]["upload"]["status"] == "success"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.upload_fixed_svg")
    def test_failure(self, mock_upload, tmp_path):
        svg = tmp_path / "test.svg"
        svg.write_text("<svg/>")
        mock_upload.return_value = {"ok": False, "error": "permission_denied"}
        proc = _make_processor()
        proc.result["stages"]["verify"]["status"] = "success"
        proc.result["file_result"] = {"path": str(svg), "nested_tags_fixed": 2}
        result = proc._upload_step()
        assert result["success"] is False
        assert proc.result["stages"]["upload"]["status"] == "Failed"
        assert "permission_denied" in result["error"]


# ---------------------------------------------------------------------------
# _run_stage
# ---------------------------------------------------------------------------

class TestRunStage:
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.save_job_result_by_name")
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.is_job_cancelled", return_value=False)
    def test_success_returns_true(self, _cancel, _save):
        proc = _make_processor()
        result = proc._run_stage("download", lambda: {"success": True, "message": "ok"})
        assert result is True
        assert proc.result["stages"]["download"]["status"] == "Completed"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.save_job_result_by_name")
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.is_job_cancelled", return_value=False)
    def test_failure_returns_false(self, _cancel, _save):
        proc = _make_processor()
        result = proc._run_stage("download", lambda: {"success": False, "error": "oops"})
        assert result is False
        assert proc.result["stages"]["download"]["status"] == "Failed"
        assert proc.result["status"] == "Failed"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.save_job_result_by_name")
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.is_job_cancelled", return_value=False)
    def test_none_success_treated_as_skipped(self, _cancel, _save):
        proc = _make_processor()
        result = proc._run_stage("analyze", lambda: {"success": None, "error": "skipped"})
        assert result is False
        assert proc.result["stages"]["analyze"]["status"] == "skipped"

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.save_job_result_by_name")
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.is_job_cancelled", return_value=False)
    def test_exception_marks_failed(self, _cancel, _save):
        proc = _make_processor()

        def boom():
            raise ValueError("unexpected!")

        result = proc._run_stage("download", boom)
        assert result is False
        assert proc.result["stages"]["download"]["status"] == "Failed"
        assert "unexpected!" in proc.result["stages"]["download"]["message"]

    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.save_job_result_by_name")
    @patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.is_job_cancelled", return_value=True)
    def test_cancelled_before_stage(self, _cancel, _save):
        proc = _make_processor()
        called = []
        result = proc._run_stage("download", lambda: called.append(1) or {"success": True})
        assert result is False
        assert called == []  # step func never called


# ---------------------------------------------------------------------------
# run() – integration-style tests (all external I/O mocked)
# ---------------------------------------------------------------------------

class TestRun:
    def _patch_all(self):
        """Return a dict of active patches for the happy-path run."""
        return {
            "create_commons_session": patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.create_commons_session"),
            "get_user_site": patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.get_user_site"),
            "download_svg_file": patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.download_svg_file"),
            "detect_nested_tags": patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.detect_nested_tags"),
            "fix_nested_tags": patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.fix_nested_tags"),
            "verify_fix": patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.verify_fix"),
            "upload_fixed_svg": patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.upload_fixed_svg"),
            "save_job": patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.save_job_result_by_name"),
            "is_cancelled": patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.is_job_cancelled", return_value=False),
        }

    def test_run_happy_path(self, tmp_path):
        svg = tmp_path / "test.svg"
        svg.write_text("<svg/>")

        patches = self._patch_all()
        mocks = {k: p.start() for k, p in patches.items()}
        try:
            mocks["download_svg_file"].return_value = {"ok": True, "path": svg}
            mocks["detect_nested_tags"].return_value = {"count": 2, "tags": ["<g>", "<g>"]}
            mocks["fix_nested_tags"].return_value = True
            mocks["verify_fix"].return_value = {"after": 0, "fixed": 2}
            mocks["upload_fixed_svg"].return_value = {"ok": True}
            mocks["get_user_site"].return_value = MagicMock()

            proc = _make_processor(filename="File:test.svg")
            result = proc.run()

            assert result["status"] == "completed"
            assert "completed_at" in result
        finally:
            for p in patches.values():
                p.stop()

    def test_run_no_filename(self):
        with patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.create_commons_session"), \
                patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.get_user_site"), \
                patch("src.main_app.public_jobs_workers.fix_nested_jobs.job.jobs_service.save_job_result_by_name"):
            proc = FixNestedJobsProcessor(
                task_id=1,
                args={},
                user={},
                result=_make_result(),
                result_file="r.json",
            )
            result = proc.run()
            assert result["status"] == "Failed"

    def test_run_upload_disabled(self, tmp_path):
        svg = tmp_path / "test.svg"
        svg.write_text("<svg/>")

        patches = self._patch_all()
        mocks = {k: p.start() for k, p in patches.items()}
        try:
            mocks["download_svg_file"].return_value = {"ok": True, "path": svg}
            mocks["detect_nested_tags"].return_value = {"count": 1, "tags": ["<g>"]}
            mocks["fix_nested_tags"].return_value = True
            mocks["verify_fix"].return_value = {"after": 0, "fixed": 1}
            mocks["get_user_site"].return_value = MagicMock()

            proc = _make_processor(filename="File:test.svg", upload=False)
            result = proc.run()

            assert result["status"] == "completed"
            assert result["stages"]["upload"]["status"] == "skipped"
            mocks["upload_fixed_svg"].assert_not_called()
        finally:
            for p in patches.values():
                p.stop()

    def test_run_auth_failure_skips_upload(self, tmp_path):
        svg = tmp_path / "test.svg"
        svg.write_text("<svg/>")

        patches = self._patch_all()
        mocks = {k: p.start() for k, p in patches.items()}
        try:
            mocks["download_svg_file"].return_value = {"ok": True, "path": svg}
            mocks["detect_nested_tags"].return_value = {"count": 1, "tags": ["<g>"]}
            mocks["fix_nested_tags"].return_value = True
            mocks["verify_fix"].return_value = {"after": 0, "fixed": 1}
            mocks["get_user_site"].return_value = None  # auth failed

            proc = _make_processor(filename="File:test.svg")
            proc.site = None
            result = proc.run()

            assert result["status"] == "Failed"
            assert result["stages"]["upload"]["status"] == "Failed"
        finally:
            for p in patches.values():
                p.stop()

    def test_run_stops_at_download_failure(self, tmp_path):
        patches = self._patch_all()
        mocks = {k: p.start() for k, p in patches.items()}
        try:
            mocks["download_svg_file"].return_value = {"ok": False, "error": "http_error"}
            mocks["get_user_site"].return_value = MagicMock()

            proc = _make_processor(filename="File:test.svg")
            result = proc.run()

            assert result["status"] == "Failed"
            mocks["detect_nested_tags"].assert_not_called()
        finally:
            for p in patches.values():
                p.stop()
