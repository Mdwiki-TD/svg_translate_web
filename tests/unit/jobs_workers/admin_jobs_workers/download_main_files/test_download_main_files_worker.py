"""Unit tests for download_main_files worker module."""

from __future__ import annotations

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker import DownloadMainFilesWorker

class TestDownloadMainFilesWorkerApplyLimits:
    def test_apply_limits_with_limit_set(self):
        templates = [TemplateRecord(id=1, title="T1", main_file="f1"), TemplateRecord(id=2, title="T2", main_file="f2")]
        w = DownloadMainFilesWorker(job_id=1, user=None, args={"limit_items": 1})
        result = w._apply_limits(templates)
        assert len(result) == 1

    def test_apply_limits_with_zero_limit(self):
        templates = [TemplateRecord(id=1, title="T1", main_file="f1")]
        w = DownloadMainFilesWorker(job_id=1, user=None, args={"limit_items": 0})
        result = w._apply_limits(templates)
        assert len(result) == 1
