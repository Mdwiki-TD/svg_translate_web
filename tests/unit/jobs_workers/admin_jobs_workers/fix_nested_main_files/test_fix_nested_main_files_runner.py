"""Unit tests for fix_nested_main_files runner module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.runner import fix_nested_main_files_for_templates
from src.main_app.shared.fix_nested.worker import (
    DetectionResult,
    VerificationResult,
)


@pytest.fixture
def mock_services(mock_before_run, monkeypatch: pytest.MonkeyPatch, mock_base_worker):
    """Mock the services used by fix_nested_main_files worker."""

    mocks = {
        "list_templates": MagicMock(),
        "update_job_status": MagicMock(),
        "save_job_result_by_name": MagicMock(),
        "download_svg_file": MagicMock(),
        "detect_nested_tags": MagicMock(),
        "fix_nested_tags": MagicMock(),
        "verify_fix": MagicMock(),
        "upload_fixed_svg": MagicMock(),
        "get_user_site": mock_base_worker["get_user_site"],
    }

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.list_templates",
        mocks["list_templates"],
    )
    monkeypatch.setattr("src.main_app.jobs_workers.base_worker.update_job_status", mocks["update_job_status"])
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name", mocks["save_job_result_by_name"]
    )

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.download_svg_file",
        mocks["download_svg_file"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.detect_nested_tags",
        mocks["detect_nested_tags"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.fix_nested_tags",
        mocks["fix_nested_tags"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.verify_fix",
        mocks["verify_fix"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.upload_fixed_svg",
        mocks["upload_fixed_svg"],
    )

    return mocks

def test_fix_nested_main_files_with_no_templates(mock_services):
    """Test worker entry point when no templates exist."""
    mock_services["list_templates"].return_value = []

    fix_nested_main_files_for_templates(job_id=1, user=None)

    assert mock_services["save_job_result_by_name"].called
    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 0


def test_fix_nested_main_files_skips_templates_without_main_file(mock_services):
    """Test that templates without main_file are skipped."""
    templates = [TemplateRecord(id=1, title="T1", main_file=None)]
    mock_services["list_templates"].return_value = templates

    fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 1
    assert result_dict["summary"]["processed"] == 1
    assert len(result_dict["pages_skipped"]) == 1
    assert "No main_file set" in result_dict["pages_skipped"][0]["message"]


def test_fix_nested_main_files_processes_template_with_main_file(mock_services):
    """Test successful processing of a template with main_file."""
    templates = [TemplateRecord(id=1, title="T1", main_file="file1.svg")]
    mock_services["list_templates"].return_value = templates

    # Mock repair utility to succeed
    mock_services["download_svg_file"].return_value = {"ok": True, "path": Path("path")}
    mock_services["detect_nested_tags"].return_value = DetectionResult(count=1)
    mock_services["fix_nested_tags"].return_value = True
    mock_services["verify_fix"].return_value = VerificationResult(before=1, after=0, fixed=1)
    mock_services["upload_fixed_svg"].return_value = {"ok": True, "result": {}}

    fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_success"]) == 1


def test_fix_nested_main_files_handles_failed_fix(mock_services):
    """Test handled failure when repair utility returns success=False."""
    templates = [TemplateRecord(id=1, title="T1", main_file="fail.svg")]
    mock_services["list_templates"].return_value = templates

    # Mock download success but no tags found (which counts as handled success=False in repair utility)
    mock_services["download_svg_file"].return_value = {"ok": True, "path": Path("path")}
    mock_services["detect_nested_tags"].return_value = DetectionResult(count=0)

    fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_skipped"]) == 1
    assert "No nested tags found" in result_dict["pages_skipped"][0]["message"]


def test_fix_nested_main_files_handles_exception(mock_services):
    """Test handled exception during template processing."""
    templates = [TemplateRecord(id=1, title="T1", main_file="error.svg")]
    mock_services["list_templates"].return_value = templates
    mock_services["download_svg_file"].side_effect = Exception("Fatal repair error")

    fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_failed"]) == 1
    assert "Error downloading error.svg" in result_dict["pages_failed"][0]["message"]


def test_fix_nested_main_files_processes_multiple_templates(mock_services):
    """Test processing multiple templates with mixed results."""
    templates = [
        TemplateRecord(id=1, title="T1", main_file="success.svg"),
        TemplateRecord(id=2, title="T2", main_file="fail.svg"),
    ]
    mock_services["list_templates"].return_value = templates

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

    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_success"]) == 1
    assert len(result_dict["pages_failed"]) == 1


def test_fix_nested_worker_handles_failed_fix_without_no_nested_tags(mock_services):
    """Test handled failure that is NOT a 'no nested tags' case."""
    templates = [TemplateRecord(id=1, title="T1", main_file="bad.svg")]
    mock_services["list_templates"].return_value = templates

    # repair utility returns success=False and NO no_nested_tags flag
    with patch(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.repair_nested_svg_tags"
    ) as mock_repair:
        mock_repair.return_value = {"success": False, "message": "Actual Error"}
        fix_nested_main_files_for_templates(job_id=1, user=None)

    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["pages_failed"]) == 1


def test_fix_nested_main_files_for_templates_accepts_args_keyword_param(mock_services):
    """Test entry point unified signature."""
    mock_services["list_templates"].return_value = []
    fix_nested_main_files_for_templates(job_id=1, user=None, args={"some": "val"})

    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 0


def test_fix_nested_main_files_for_templates_args_defaults_to_none(mock_services):
    """Test entry point defaults args to None."""
    mock_services["list_templates"].return_value = []
    fix_nested_main_files_for_templates(job_id=99, user=None)

    result_dict = mock_services["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 0
