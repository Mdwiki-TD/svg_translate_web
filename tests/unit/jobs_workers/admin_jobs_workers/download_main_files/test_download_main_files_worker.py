"""Unit tests for download_main_files worker module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.download_main_files import worker


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch, mock_before_run):
    """Mock the services used by download_main_files worker."""

    mocks = {
        "list_templates": MagicMock(),
        "download_file_from_commons": MagicMock(),
        "generate_main_files_zip": MagicMock(),
        "create_commons_session": MagicMock(),
        "download_commons_file_core": MagicMock(return_value=b"svg-content"),
        "before_run": mock_before_run,
    }

    # Mock template_service
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.list_templates",
        mocks["list_templates"],
    )

    # Mock api_services
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.download_file_from_commons",
        mocks["download_file_from_commons"],
    )

    # Mock zip generation
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.generate_main_files_zip",
        mocks["generate_main_files_zip"],
    )

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.create_commons_session",
        mocks["create_commons_session"],
    )

    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.download_helper.download_commons_file_core",
        mocks["download_commons_file_core"],
    )
    return mocks


class TestDownloadMainFilesWorkerApplyLimits:
    def test_apply_limits_with_limit_set(self):
        templates = [TemplateRecord(id=1, title="T1", main_file="f1"), TemplateRecord(id=2, title="T2", main_file="f2")]
        w = worker.DownloadMainFilesWorker(job_id=1, user=None, args={"limit_items": 1})
        result = w._apply_limits(templates)
        assert len(result) == 1

    def test_apply_limits_with_zero_limit(self):
        templates = [TemplateRecord(id=1, title="T1", main_file="f1")]
        w = worker.DownloadMainFilesWorker(job_id=1, user=None, args={"limit_items": 0})
        result = w._apply_limits(templates)
        assert len(result) == 1
