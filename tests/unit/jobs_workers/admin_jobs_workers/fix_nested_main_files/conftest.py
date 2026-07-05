"""Unit tests for fix_nested_main_files worker module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

@pytest.fixture
def mock_fix_nested_services(mock_before_run, monkeypatch: pytest.MonkeyPatch, mock_base_worker):
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

