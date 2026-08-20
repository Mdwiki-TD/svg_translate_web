"""Unit tests for fix_nested_main_files worker module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.main_app.api_services.files_service import DownloadAndSaveData
from src.main_app.api_services.files_service.objects import UploadResult
from src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files import worker
from src.main_app.jobs_workers.objects import JobsRunner
from src.main_app.services.fix_nested.worker import (
    DetectionResult,
    VerificationResult,
)


@pytest.fixture
def mock_fix_nested_admin_services(mock_before_run, monkeypatch: pytest.MonkeyPatch, mock_base_worker):
    """Mock the services used by fix_nested_main_files worker."""

    mocks = {
        "list": MagicMock(),
        "update_job_status": MagicMock(),
        "save_job_result_by_name": MagicMock(),
        "download_and_save": MagicMock(),
        "detect_nested_tags": MagicMock(),
        "repair_file": MagicMock(),
        "verify_fix": MagicMock(),
        "upload_svg": MagicMock(),
        "get_user_site": mock_base_worker["get_user_site"],
    }

    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.JobsService.update_job_status", mocks["update_job_status"]
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name", mocks["save_job_result_by_name"]
    )

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.TemplateService.list",
        mocks["list"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.FilesService.download_and_save",
        mocks["download_and_save"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.UploadService.upload_svg",
        mocks["upload_svg"],
    )

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.detect_nested_tags",
        mocks["detect_nested_tags"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.repair_file",
        mocks["repair_file"],
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files.worker.verify_fix",
        mocks["verify_fix"],
    )

    return mocks


def test_repair_nested_svg_tags_success(mock_fix_nested_admin_services, tmp_path):
    """Test successful high-level orchestration for a single file."""
    filename = "Test.svg"
    user = {"username": "tester"}

    mock_fix_nested_admin_services["download_and_save"].return_value = DownloadAndSaveData(
        result="success", path=Path("tmp/path.svg")
    )
    mock_fix_nested_admin_services["detect_nested_tags"].return_value = DetectionResult(count=5)
    mock_fix_nested_admin_services["repair_file"].return_value = True
    mock_fix_nested_admin_services["verify_fix"].return_value = VerificationResult(before=5, after=0, fixed=5)
    mock_fix_nested_admin_services["upload_svg"].return_value = UploadResult(ok=True, result={"newrevid": 123})

    data = JobsRunner(job_id=0, user=user)
    result = worker.FixNestedMainFilesWorker(data).repair_nested_svg_tags(filename, tmp_path)

    assert result["success"] is True
    assert "Successfully fixed 5 nested tag(s)" in result["message"]
    mock_fix_nested_admin_services["upload_svg"].assert_called_once()


def test_repair_nested_svg_tags_no_tags(mock_fix_nested_admin_services, tmp_path):
    """Test behavior when no nested tags are detected."""
    mock_fix_nested_admin_services["download_and_save"].return_value = DownloadAndSaveData(
        result="success", path=Path("tmp/path.svg")
    )
    mock_fix_nested_admin_services["detect_nested_tags"].return_value = DetectionResult(count=0)

    data = JobsRunner(job_id=0, user={})
    result = worker.FixNestedMainFilesWorker(data).repair_nested_svg_tags("Clean.svg", tmp_path)

    assert result["success"] is False
    assert result["no_nested_tags"] is True
    assert "No nested tags found" in result["message"]
