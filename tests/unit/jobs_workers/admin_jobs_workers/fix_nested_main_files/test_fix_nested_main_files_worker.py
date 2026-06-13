"""Unit tests for fix_nested_main_files worker module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files import worker
from src.main_app.shared.fix_nested.objects import (
    DetectionResult,
    DownloadResult,
    UploadResult,
    VerificationResult,
)


@pytest.fixture
def mock_fix_nested_services(monkeypatch: pytest.MonkeyPatch, mock_jobs_service):
    """Mock the services used by fix_nested_main_files worker."""

    # Mock template_service
    mock_list_templates = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.list_templates", mock_list_templates
    )

    # Mock jobs_service (base worker)
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock()
    monkeypatch.setattr("src.main_app.jobs_workers.base_worker_object.update_job_status", mock_update_job_status)
    monkeypatch.setattr("src.main_app.jobs_workers.base_worker_object.save_job_result_by_name", mock_save_job_result)

    # Bypass BaseObjectsJobWorker.before_run
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker_object.BaseObjectsJobWorker.before_run",
        MagicMock(return_value=True),
    )

    # Mock shared fix_nested utilities
    mock_download_svg = MagicMock()
    mock_detect_nested = MagicMock()
    mock_fix_nested = MagicMock()
    mock_verify_fix = MagicMock()
    mock_upload_fixed = MagicMock()

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.download_svg_file", mock_download_svg
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.detect_nested_tags",
        mock_detect_nested,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.fix_nested_tags", mock_fix_nested
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.verify_fix", mock_verify_fix
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.upload_fixed_svg", mock_upload_fixed
    )

    return {
        "list_templates": mock_list_templates,
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "download_svg_file": mock_download_svg,
        "detect_nested_tags": mock_detect_nested,
        "fix_nested_tags": mock_fix_nested,
        "verify_fix": mock_verify_fix,
        "upload_fixed_svg": mock_upload_fixed,
    }


def test_repair_nested_svg_tags_success(mock_fix_nested_services):
    """Test successful high-level orchestration for a single file."""
    filename = "Test.svg"
    user = {"username": "tester"}

    mock_fix_nested_services["download_svg_file"].return_value = DownloadResult(ok=True, path=Path("tmp/path.svg"))
    mock_fix_nested_services["detect_nested_tags"].return_value = DetectionResult(count=5)
    mock_fix_nested_services["fix_nested_tags"].return_value = True
    mock_fix_nested_services["verify_fix"].return_value = VerificationResult(before=5, after=0, fixed=5)
    mock_fix_nested_services["upload_fixed_svg"].return_value = UploadResult(ok=True, result={"newrevid": 123})

    result = worker.repair_nested_svg_tags(filename, user)

    assert result["success"] is True
    assert "Successfully fixed 5 nested tag(s)" in result["message"]
    mock_fix_nested_services["upload_fixed_svg"].assert_called_once()


def test_repair_nested_svg_tags_no_tags(mock_fix_nested_services):
    """Test behavior when no nested tags are detected."""
    mock_fix_nested_services["download_svg_file"].return_value = DownloadResult(ok=True, path=Path("tmp/path.svg"))
    mock_fix_nested_services["detect_nested_tags"].return_value = DetectionResult(count=0)

    result = worker.repair_nested_svg_tags("Clean.svg", {})

    assert result["success"] is False
    assert result["no_nested_tags"] is True
    assert "No nested tags found" in result["message"]


def test_fix_nested_main_files_with_no_templates(mock_fix_nested_services):
    """Test worker entry point when no templates exist."""
    mock_fix_nested_services["list_templates"].return_value = []

    worker.fix_nested_main_files_for_templates(job_id=1, user=None)

    assert mock_fix_nested_services["save_job_result_by_name"].called
    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 0


def test_fix_nested_main_files_skips_templates_without_main_file(mock_fix_nested_services):
    """Test that templates without main_file are skipped."""
    templates = [TemplateRecord(id=1, title="T1", main_file=None)]
    mock_fix_nested_services["list_templates"].return_value = templates

    worker.fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 1
    assert result_dict["summary"]["processed"] == 1
    assert len(result_dict["pages_skipped"]) == 1
    assert "No main_file set" in result_dict["pages_skipped"][0]["reason"]


def test_fix_nested_main_files_processes_template_with_main_file(mock_fix_nested_services):
    """Test successful processing of a template with main_file."""
    templates = [TemplateRecord(id=1, title="T1", main_file="file1.svg")]
    mock_fix_nested_services["list_templates"].return_value = templates

    # Mock repair utility to succeed
    mock_fix_nested_services["download_svg_file"].return_value = DownloadResult(ok=True, path=Path("path"))
    mock_fix_nested_services["detect_nested_tags"].return_value = DetectionResult(count=1)
    mock_fix_nested_services["fix_nested_tags"].return_value = True
    mock_fix_nested_services["verify_fix"].return_value = VerificationResult(before=1, after=0, fixed=1)
    mock_fix_nested_services["upload_fixed_svg"].return_value = UploadResult(ok=True, result={})

    worker.fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["success"] == 1
    assert len(result_dict["pages_success"]) == 1


def test_fix_nested_main_files_handles_failed_fix(mock_fix_nested_services):
    """Test handled failure when repair utility returns success=False."""
    templates = [TemplateRecord(id=1, title="T1", main_file="fail.svg")]
    mock_fix_nested_services["list_templates"].return_value = templates

    # Mock download success but no tags found (which counts as handled success=False in repair utility)
    mock_fix_nested_services["download_svg_file"].return_value = DownloadResult(ok=True, path=Path("path"))
    mock_fix_nested_services["detect_nested_tags"].return_value = DetectionResult(count=0)

    worker.fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["skipped"] == 1
    assert len(result_dict["pages_skipped"]) == 1
    assert "No nested tags found" in result_dict["pages_skipped"][0]["reason"]


def test_fix_nested_main_files_handles_exception(mock_fix_nested_services):
    """Test handled exception during template processing."""
    templates = [TemplateRecord(id=1, title="T1", main_file="error.svg")]
    mock_fix_nested_services["list_templates"].return_value = templates
    mock_fix_nested_services["download_svg_file"].side_effect = Exception("Fatal repair error")

    worker.fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["failed"] == 1
    assert "Exception: Fatal repair error" in result_dict["pages_failed"][0]["reason"]


def test_fix_nested_main_files_processes_multiple_templates(mock_fix_nested_services):
    """Test processing multiple templates with mixed results."""
    templates = [
        TemplateRecord(id=1, title="T1", main_file="success.svg"),
        TemplateRecord(id=2, title="T2", main_file="fail.svg"),
    ]
    mock_fix_nested_services["list_templates"].return_value = templates

    def repair_side_effect(filename, *args, **kwargs):
        if filename == "success.svg":
            return {"success": True, "message": "OK", "details": {}}
        return {"success": False, "message": "Fail", "details": {}}

    # We need to patch repair_nested_svg_tags directly since it's a module level function
    with patch(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.repair_nested_svg_tags"
    ) as mock_repair:
        mock_repair.side_effect = repair_side_effect
        worker.fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["success"] == 1
    assert result_dict["summary"]["failed"] == 1


def test_fix_nested_worker_handles_failed_fix_without_no_nested_tags(mock_fix_nested_services):
    """Test handled failure that is NOT a 'no nested tags' case."""
    templates = [TemplateRecord(id=1, title="T1", main_file="bad.svg")]
    mock_fix_nested_services["list_templates"].return_value = templates

    # repair utility returns success=False and NO no_nested_tags flag
    with patch(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.repair_nested_svg_tags"
    ) as mock_repair:
        mock_repair.return_value = {"success": False, "message": "Actual Error"}
        worker.fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["failed"] == 1


def test_fix_nested_main_files_for_templates_accepts_args_keyword_param(mock_fix_nested_services):
    """Test entry point unified signature."""
    mock_fix_nested_services["list_templates"].return_value = []
    worker.fix_nested_main_files_for_templates(job_id=1, user=None, args={"some": "val"})

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 0


def test_fix_nested_main_files_for_templates_args_defaults_to_none(mock_fix_nested_services):
    """Test entry point defaults args to None."""
    mock_fix_nested_services["list_templates"].return_value = []
    worker.fix_nested_main_files_for_templates(job_id=99, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 0
