"""Unit tests for crop_main_files.worker module."""

from __future__ import annotations

import threading
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.admin_jobs_workers.crop_main_files import worker
from src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.objects import CropMainFilesWorkerObject


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    """Mock the services used by worker module."""
    mock_update_job_status_with_retry = MagicMock()
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.update_job_status",
        mock_update_job_status,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.update_job_status_with_retry",
        mock_update_job_status_with_retry,
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.save_job_result_by_name",
        mock_save_job_result,
    )

    mock_generate_result_file_name = MagicMock(side_effect=lambda job_id, job_type: f"{job_type}_job_{job_id}.json")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.generate_result_file_name",
        mock_generate_result_file_name,
    )

    # Bypass BaseObjectsJobWorker.before_run
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.BaseObjectsJobWorker.before_run", MagicMock(return_value=True)
    )

    return {
        "update_job_status_with_retry": mock_update_job_status_with_retry,
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "generate_result_file_name": mock_generate_result_file_name,
    }



# ---------------------------------------------------------------------------
# Fixture for a completed result returned by process()
# ---------------------------------------------------------------------------


def make_completed_result(summary_overrides=None):
    """Return a standard completed-result object for use in mock process()."""
    result = CropMainFilesWorkerObject()
    result.status = "completed"
    result.summary.total = 10
    result.summary.processed = 10
    result.summary.cropped = 8
    result.summary.uploaded = 0
    result.summary.failed = 2
    result.summary.skipped = 0

    if summary_overrides:
        for k, v in summary_overrides.items():
            setattr(result.summary, k, v)
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_crop_main_files_worker_entry_basic_flow(mock_services):
    """Test basic flow of crop_main_files_worker_entry."""
    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result()

        worker.crop_main_files_worker_entry(job_id=1, user=None)

    mock_process.assert_called_once()

    # Verify final status was updated via after_run()
    final_call = mock_services["update_job_status_with_retry"].call_args
    assert final_call[0][0] == 1
    assert final_call[0][1] == "completed"


def test_crop_main_files_worker_entry_initializes_result(mock_services):
    """Test that result structure is properly initialized."""
    w = worker.CropMainFilesWorker(job_id=1, user=None)
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


def test_crop_main_files_worker_entry_with_user(mock_services):
    """Test crop_main_files_worker_entry passes user to CropMainFilesWorker."""
    user = {"username": "testuser"}

    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result({"total": 5, "processed": 5, "cropped": 5, "uploaded": 5})

        worker.crop_main_files_worker_entry(job_id=1, user=user)

    # Verify the entry point runs and process is called
    mock_process.assert_called_once()

    # Verify final status is updated
    final_call = mock_services["update_job_status_with_retry"].call_args
    assert final_call[0][1] == "completed"


def test_crop_main_files_worker_entry_with_cancel_event(mock_services):
    """Test crop_main_files_worker_entry passes cancel_event to CropMainFilesWorker."""
    cancel_event = threading.Event()

    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        cancelled_result = make_completed_result()
        cancelled_result.status = "cancelled"
        cancelled_result.cancelled_at = datetime.now().isoformat()
        mock_process.return_value = cancelled_result

        worker.crop_main_files_worker_entry(job_id=1, user=None, cancel_event=cancel_event)

    mock_process.assert_called_once()
    # Verify cancelled status is preserved
    final_call = mock_services["update_job_status_with_retry"].call_args
    assert final_call[0][1] == "cancelled"


def test_crop_main_files_worker_entry_handles_exception(mock_services):
    """Test that exceptions during processing are handled gracefully."""
    mock_services["save_job_result_by_name"].reset_mock()

    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.side_effect = RuntimeError("Database connection failed")

        worker.crop_main_files_worker_entry(job_id=1, user=None)

    # after_run() saves the final result
    save_calls = mock_services["save_job_result_by_name"].call_args_list
    assert len(save_calls) >= 1

    # Check the last saved result has error details
    last_saved = save_calls[-1][0][1]
    assert last_saved["status"] == "failed"
    assert "Database connection failed" in last_saved["errors"][0]["error"]
    assert last_saved["errors"][0]["error_type"] == "RuntimeError"


def test_crop_main_files_worker_entry_sets_completed_timestamp(mock_services):
    """Test that completed_at timestamp is set."""
    mock_services["save_job_result_by_name"].reset_mock()

    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result()

        worker.crop_main_files_worker_entry(job_id=1, user=None)

    # Verify completed_at was set by after_run()
    save_calls = mock_services["save_job_result_by_name"].call_args_list
    assert len(save_calls) >= 1
    last_saved = save_calls[-1][0][1]
    assert last_saved["completed_at"] is not None
    datetime.fromisoformat(last_saved["completed_at"])


def test_crop_main_files_worker_entry_saves_final_result(mock_services):
    """Test that final result is saved."""
    mock_services["save_job_result_by_name"].reset_mock()

    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result({"total": 3, "processed": 3, "cropped": 3, "skipped": 3})

        worker.crop_main_files_worker_entry(job_id=1, user=None)

    save_calls = mock_services["save_job_result_by_name"].call_args_list
    assert len(save_calls) >= 1
    call_args = save_calls[-1]
    assert call_args[0][0] == "crop_main_files_job_1.json"


def test_crop_main_files_worker_entry_updates_final_status(mock_services):
    """Test that final job status is updated."""
    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result(
            {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0}
        )

        worker.crop_main_files_worker_entry(job_id=1, user=None)

    final_call = mock_services["update_job_status_with_retry"].call_args
    assert final_call[0][0] == 1
    assert final_call[0][1] == "completed"
    assert final_call[0][2] == "crop_main_files_job_1.json"
    assert final_call[1]["job_type"] == "crop_main_files"


def test_crop_main_files_worker_entry_handles_save_failure(mock_services):
    """Test that failures to save results are handled gracefully."""
    mock_services["save_job_result_by_name"].side_effect = Exception("Disk full")

    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result(
            {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0}
        )

        # Should not raise exception
        worker.crop_main_files_worker_entry(job_id=1, user=None)


def test_crop_main_files_worker_entry_handles_status_update_failure(mock_services):
    """Test that failures to update status are handled gracefully."""
    mock_services["update_job_status"].side_effect = LookupError("Job not found")

    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result(
            {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0}
        )

        # Should not raise exception
        worker.crop_main_files_worker_entry(job_id=1, user=None)


def test_crop_main_files_worker_entry_generates_correct_result_file_name(mock_services):
    """Test that result file name is generated correctly."""
    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result(
            {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0}
        )

        worker.crop_main_files_worker_entry(job_id=1, user=None)

    mock_services["generate_result_file_name"].assert_called_once_with(1, "crop_main_files")


def test_crop_main_files_worker_entry_passes_result_file_to_process(mock_services):
    """Test that result_file is available on the worker."""
    mock_services["save_job_result_by_name"].reset_mock()

    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result(
            {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0}
        )

        worker.crop_main_files_worker_entry(job_id=1, user=None)

    # Verify result was saved with correct file name
    save_calls = mock_services["save_job_result_by_name"].call_args_list
    assert len(save_calls) >= 1
    assert save_calls[-1][0][0] == "crop_main_files_job_1.json"


def test_crop_main_files_worker_entry_preserves_cancelled_status(mock_services):
    """Test that cancelled status is preserved in final update."""
    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        cancelled_result = make_completed_result()
        cancelled_result.status = "cancelled"
        cancelled_result.cancelled_at = datetime.now().isoformat()
        cancelled_result.summary.total = 5
        cancelled_result.summary.processed = 2
        cancelled_result.summary.cropped = 2

        mock_process.return_value = cancelled_result

        worker.crop_main_files_worker_entry(job_id=1, user=None)

    final_call = mock_services["update_job_status_with_retry"].call_args
    assert final_call[0][1] == "cancelled"


def test_crop_main_files_worker_entry_preserves_failed_status(mock_services):
    """Test that failed status from process is preserved."""
    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        failed_result = make_completed_result()
        failed_result.status = "failed"
        failed_result.summary.total = 5
        failed_result.summary.failed = 5
        mock_process.return_value = failed_result

        worker.crop_main_files_worker_entry(job_id=1, user=None)

    final_call = mock_services["update_job_status_with_retry"].call_args
    assert final_call[0][1] == "failed"


def test_crop_main_files_worker_entry_different_exception_types(mock_services):
    """Test handling of different exception types."""
    exception_types = [
        (ValueError("Invalid value"), "ValueError"),
        (KeyError("Missing key"), "KeyError"),
        (OSError("File not found"), "OSError"),
        (Exception("Generic error"), "Exception"),
    ]

    for exception, expected_type in exception_types:
        mock_services["save_job_result_by_name"].reset_mock()
        mock_services["update_job_status"].reset_mock()

        with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
            mock_process.side_effect = exception

            worker.crop_main_files_worker_entry(job_id=1, user=None)

        save_calls = mock_services["save_job_result_by_name"].call_args_list
        assert len(save_calls) >= 1
        last_saved = save_calls[-1][0][1]
        assert last_saved["errors"][0]["error_type"] == expected_type


def test_crop_main_files_worker_entry_upload_files_flag(mock_services):
    """Test that upload_files is True in the worker's process method."""
    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result(
            {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0}
        )

        worker.crop_main_files_worker_entry(job_id=1, user=None)

    mock_process.assert_called_once()


def test_crop_main_files_worker_entry_multiple_jobs(mock_services):
    """Test running multiple jobs with different IDs."""
    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result(
            {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0}
        )

        worker.crop_main_files_worker_entry(job_id=1, user=None)
        worker.crop_main_files_worker_entry(job_id=2, user=None)
        worker.crop_main_files_worker_entry(job_id=3, user=None)

    assert mock_services["generate_result_file_name"].call_count == 3
    calls = mock_services["generate_result_file_name"].call_args_list
    assert calls[0][0] == (1, "crop_main_files")
    assert calls[1][0] == (2, "crop_main_files")
    assert calls[2][0] == (3, "crop_main_files")


def test_crop_main_files_worker_entry_started_at_timestamp(mock_services):
    """Test that started_at timestamp is set correctly."""
    w = worker.CropMainFilesWorker(job_id=1, user=None)
    result = w.result
    assert result.started_at is not None
    datetime.fromisoformat(result.started_at)


def test_crop_main_files_worker_entry_exception_includes_traceback_in_logs(mock_services):
    """Test that exceptions are logged with full traceback."""
    with (
        patch.object(worker.CropMainFilesWorker, "process") as mock_process,
        patch("src.main_app.jobs_workers.base_worker.logger") as mock_logger,
    ):
        mock_process.side_effect = RuntimeError("Test error")

        worker.crop_main_files_worker_entry(job_id=1, user=None)

    # handle_error() calls logger.exception()
    mock_logger.exception.assert_called_once()


def test_crop_main_files_worker_entry_completed_status_default(mock_services):
    """Test that default status is completed when no other status is set."""
    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result()

        worker.crop_main_files_worker_entry(job_id=1, user=None)

    final_call = mock_services["update_job_status_with_retry"].call_args
    assert final_call[0][1] == "completed"


def test_crop_main_files_worker_entry_accepts_args_keyword_param(mock_services):
    """Test that crop_main_files_worker_entry accepts args= keyword-only param (unified signature)."""
    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result(
            {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0}
        )

        # Should not raise TypeError
        worker.crop_main_files_worker_entry(job_id=1, user=None, args={"some_key": "value"})

    mock_process.assert_called_once()


def test_crop_main_files_worker_reads_upload_limit_from_args(mock_services):
    """Test CropMainFilesWorker reads upload_limit from args."""
    w = worker.CropMainFilesWorker(job_id=1, user=None, cancel_event=None, args={"upload_limit": 5})
    assert w.upload_limit == 5


def test_crop_main_files_worker_defaults_upload_limit_when_args_none(mock_services):
    """Test CropMainFilesWorker defaults upload_limit to None when args is None."""
    w = worker.CropMainFilesWorker(job_id=1, user=None, cancel_event=None, args=None)
    assert w.upload_limit == 0


def test_crop_main_files_worker_defaults_upload_limit_when_key_missing(mock_services):
    """Test CropMainFilesWorker defaults upload_limit to None when key is missing."""
    w = worker.CropMainFilesWorker(job_id=1, user=None, cancel_event=None, args={"other_key": "value"})
    assert w.upload_limit == 0


def test_crop_main_files_worker_entry_args_defaults_to_none(mock_services):
    """Test that args defaults to None and entry point works without it."""
    with patch.object(worker.CropMainFilesWorker, "process") as mock_process:
        mock_process.return_value = make_completed_result(
            {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0}
        )

        worker.crop_main_files_worker_entry(job_id=2, user=None)

    mock_process.assert_called_once()


def test_crop_main_files_worker_entry_maps_crop_newest_upload_limit(mock_services):
    """Test that upload_limit is mapped to upload_limit in args."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.CropMainFilesWorker") as MockWorker:
        mock_instance = MagicMock()
        MockWorker.return_value = mock_instance

        worker.crop_main_files_worker_entry(job_id=1, user=None, args={"upload_limit": 3})

        call_args = MockWorker.call_args
        passed_args = call_args[0][3] if len(call_args[0]) > 3 else call_args.kwargs.get("args")
        assert passed_args is not None
        assert passed_args["upload_limit"] == 3


def test_crop_main_files_worker_entry_does_not_map_when_key_absent(mock_services):
    """Test that args are passed unchanged when upload_limit is absent."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.CropMainFilesWorker") as MockWorker:
        mock_instance = MagicMock()
        MockWorker.return_value = mock_instance

        worker.crop_main_files_worker_entry(job_id=1, user=None, args={"other_key": "value"})

        call_args = MockWorker.call_args
        passed_args = call_args[0][3] if len(call_args[0]) > 3 else call_args.kwargs.get("args")
        assert "upload_limit" not in passed_args


def test_crop_main_files_worker_entry_does_not_modify_args_when_none(mock_services):
    """Test that entry point works correctly when args is None."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.worker.CropMainFilesWorker") as MockWorker:
        mock_instance = MagicMock()
        MockWorker.return_value = mock_instance

        worker.crop_main_files_worker_entry(job_id=1, user=None, args=None)

        call_args = MockWorker.call_args
        passed_args = call_args[0][3] if len(call_args[0]) > 3 else call_args.kwargs.get("args")
        assert passed_args is None
