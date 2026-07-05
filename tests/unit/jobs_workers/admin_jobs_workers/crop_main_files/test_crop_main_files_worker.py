"""Unit tests for crop_main_files.worker module."""

from __future__ import annotations

from src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker import CropMainFilesWorker

def test_crop_main_files_worker_entry_initializes_result(mock_base_worker):
    """Test that result structure is properly initialized."""
    w = CropMainFilesWorker(job_id=1, user=None)
    result = w.result

    assert result.status == "pending"
    assert result.started_at is not None
    assert result.completed_at is None
    assert result.cancelled_at is None
    assert result.summary.total == 0
    assert result.summary.processed == 0
    assert result.summary.cropped == 0
    assert result.summary.uploaded == 0
    assert result.summary.failed == 0
    assert result.summary.skipped == 0
    assert result.pages_processed == []



def test_crop_main_files_worker_reads_upload_limit_from_args(mock_base_worker):
    """Test CropMainFilesWorker reads upload_limit from args."""
    w = CropMainFilesWorker(job_id=1, user=None, cancel_event=None, args={"upload_limit": 5})
    assert w.upload_limit == 5


def test_crop_main_files_worker_defaults_upload_limit_when_args_none(mock_base_worker):
    """Test CropMainFilesWorker defaults upload_limit to None when args is None."""
    w = CropMainFilesWorker(job_id=1, user=None, cancel_event=None, args=None)
    assert w.upload_limit == 0


def test_crop_main_files_worker_defaults_upload_limit_when_key_missing(mock_base_worker):
    """Test CropMainFilesWorker defaults upload_limit to None when key is missing."""
    w = CropMainFilesWorker(job_id=1, user=None, cancel_event=None, args={"other_key": "value"})
    assert w.upload_limit == 0

