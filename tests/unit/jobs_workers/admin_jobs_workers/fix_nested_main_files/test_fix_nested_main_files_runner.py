"""Unit tests for fix_nested_main_files runner module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.runner import (
    fix_nested_main_files_for_templates,
)
from src.main_app.shared.fix_nested.worker import (
    DetectionResult,
    VerificationResult,
)


def test_fix_nested_main_files_with_no_templates(mock_fix_nested_services):
    """Test worker entry point when no templates exist."""
    mock_fix_nested_services["list_templates"].return_value = []

    fix_nested_main_files_for_templates(job_id=1, user=None)

    assert mock_fix_nested_services["save_job_result_by_name"].called
    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 0


def test_fix_nested_main_files_skips_templates_without_main_file(mock_fix_nested_services):
    """Test that templates without main_file are skipped."""
    templates = [TemplateRecord(id=1, title="T1", main_file=None)]
    mock_fix_nested_services["list_templates"].return_value = templates

    fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 1
    assert result_dict["summary"]["processed"] == 1
    assert len(result_dict["pages_skipped"]) == 1
    assert "No main_file set" in result_dict["pages_skipped"][0]["message"]


def test_fix_nested_main_files_processes_template_with_main_file(mock_fix_nested_services):
    """Test successful processing of a template with main_file."""
    templates = [TemplateRecord(id=1, title="T1", main_file="file1.svg")]
    mock_fix_nested_services["list_templates"].return_value = templates

    # Mock repair utility to succeed
    mock_fix_nested_services["download_svg_file"].return_value = {"ok": True, "path": Path("path")}
    mock_fix_nested_services["detect_nested_tags"].return_value = DetectionResult(count=1)
    mock_fix_nested_services["fix_nested_tags"].return_value = True
    mock_fix_nested_services["verify_fix"].return_value = VerificationResult(before=1, after=0, fixed=1)
    mock_fix_nested_services["upload_fixed_svg"].return_value = {"ok": True, "result": {}}

    fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_success"]) == 1


def test_fix_nested_main_files_handles_failed_fix(mock_fix_nested_services):
    """Test handled failure when repair utility returns success=False."""
    templates = [TemplateRecord(id=1, title="T1", main_file="fail.svg")]
    mock_fix_nested_services["list_templates"].return_value = templates

    # Mock download success but no tags found (which counts as handled success=False in repair utility)
    mock_fix_nested_services["download_svg_file"].return_value = {"ok": True, "path": Path("path")}
    mock_fix_nested_services["detect_nested_tags"].return_value = DetectionResult(count=0)

    fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_skipped"]) == 1
    assert "No nested tags found" in result_dict["pages_skipped"][0]["message"]


def test_fix_nested_main_files_handles_exception(mock_fix_nested_services):
    """Test handled exception during template processing."""
    templates = [TemplateRecord(id=1, title="T1", main_file="error.svg")]
    mock_fix_nested_services["list_templates"].return_value = templates
    mock_fix_nested_services["download_svg_file"].side_effect = Exception("Fatal repair error")

    fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_failed"]) == 1
    assert "Error downloading error.svg" in result_dict["pages_failed"][0]["message"]


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
        fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_success"]) == 1
    assert len(result_dict["pages_failed"]) == 1


def test_fix_nested_worker_handles_failed_fix_without_no_nested_tags(mock_fix_nested_services):
    """Test handled failure that is NOT a 'no nested tags' case."""
    templates = [TemplateRecord(id=1, title="T1", main_file="bad.svg")]
    mock_fix_nested_services["list_templates"].return_value = templates

    # repair utility returns success=False and NO no_nested_tags flag
    with patch(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.repair_nested_svg_tags"
    ) as mock_repair:
        mock_repair.return_value = {"success": False, "message": "Actual Error"}
        fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_failed"]) == 1


def test_fix_nested_main_files_for_templates_accepts_args_keyword_param(mock_fix_nested_services):
    """Test entry point unified signature."""
    mock_fix_nested_services["list_templates"].return_value = []
    fix_nested_main_files_for_templates(job_id=1, user=None, args={"some": "val"})

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 0


def test_fix_nested_main_files_for_templates_args_defaults_to_none(mock_fix_nested_services):
    """Test entry point defaults args to None."""
    mock_fix_nested_services["list_templates"].return_value = []
    fix_nested_main_files_for_templates(job_id=99, user=None)

    result_dict = mock_fix_nested_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 0
