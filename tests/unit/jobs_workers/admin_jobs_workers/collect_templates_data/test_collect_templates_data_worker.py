"""Unit tests for collect_templates_data_worker module."""

from __future__ import annotations

from src.main_app.jobs_workers.admin_jobs_workers.collect_templates_data import worker

from ......src.main_app.jobs_workers.objects import JobsRunner


def test_worker_class_get_job_type():
    """Test CollectMainFilesWorker.get_job_type returns correct type."""
    import threading

    _worker = worker.CollectMainFilesWorker(JobsRunner(job_id=1, user=None, cancel_event=threading.Event()))
    assert _worker.get_job_type() == "collect_templates_data"


def test_worker_class_get_initial_result():
    """Test CollectMainFilesWorker initial result structure."""
    import threading

    _worker = worker.CollectMainFilesWorker(JobsRunner(job_id=1, user=None, cancel_event=threading.Event()))
    result = _worker.result

    assert result.summary.total == 0
    assert len(result.pages_added) == 0


# --- Tests for new update_all functionality (added in this PR) ---


def test_worker_init_update_all_defaults_to_false():
    """Test CollectMainFilesWorker initializes update_all=False by default."""
    import threading

    _worker = worker.CollectMainFilesWorker(JobsRunner(job_id=1, user=None, cancel_event=threading.Event()))
    assert _worker.update_all is False


def test_worker_init_update_all_can_be_set_true():
    """Test CollectMainFilesWorker accepts update_all='true' or update_all=True."""
    import threading

    _worker = worker.CollectMainFilesWorker(
        job_id=1, user=None, cancel_event=threading.Event(), args={"update_all": "true"}
    )
    assert _worker.update_all is True

    worker2 = worker.CollectMainFilesWorker(
        job_id=1, user=None, cancel_event=threading.Event(), args={"update_all": True}
    )
    assert worker2.update_all is True
