"""Unit tests for fix_nested_main_files worker module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.admin_jobs_workers.fix_nested_main_files import worker
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


def test_repair_nested_svg_tags_success(mock_services, tmp_path):
    """Test successful high-level orchestration for a single file."""
    filename = "Test.svg"
    user = {"username": "tester"}

    mock_services["download_svg_file"].return_value = {"ok": True, "path": Path("tmp/path.svg")}
    mock_services["detect_nested_tags"].return_value = DetectionResult(count=5)
    mock_services["fix_nested_tags"].return_value = True
    mock_services["verify_fix"].return_value = VerificationResult(before=5, after=0, fixed=5)
    mock_services["upload_fixed_svg"].return_value = {"ok": True, "result": {"newrevid": 123}}

    result = worker.repair_nested_svg_tags(filename, user, tmp_path)

    assert result["success"] is True
    assert "Successfully fixed 5 nested tag(s)" in result["message"]
    mock_services["upload_fixed_svg"].assert_called_once()


def test_repair_nested_svg_tags_no_tags(mock_services, tmp_path):
    """Test behavior when no nested tags are detected."""
    mock_services["download_svg_file"].return_value = {"ok": True, "path": Path("tmp/path.svg")}
    mock_services["detect_nested_tags"].return_value = DetectionResult(count=0)

    result = worker.repair_nested_svg_tags("Clean.svg", {}, tmp_path)

    assert result["success"] is False
    assert result["no_nested_tags"] is True
    assert "No nested tags found" in result["message"]
