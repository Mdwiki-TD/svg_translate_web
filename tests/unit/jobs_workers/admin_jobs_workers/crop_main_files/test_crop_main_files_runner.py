"""Unit tests for crop_main_files.worker module."""

from __future__ import annotations

import threading
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.admin_jobs_workers.crop_main_files import (
    CropMainFilesWorkerObject,
    crop_main_files_worker_entry,
)

# ---------------------------------------------------------------------------
# Fixture for a completed result returned by process()
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_instance_class(monkeypatch):
    mock_instance = MagicMock()
    mock_instance.process = MagicMock()

    _mock = MagicMock()
    _mock.return_value = mock_instance
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.runner.CropMainFilesWorker", _mock
    )
    return _mock


@pytest.fixture
def mock_process():
    with patch(
        "src.main_app.jobs_workers.admin_jobs_workers.crop_main_files.runner.CropMainFilesWorker.process"
    ) as mock:
        mock.return_value = make_completed_result(
            {"total": 0, "processed": 0, "cropped": 0, "uploaded": 0, "failed": 0, "skipped": 0}
        )
        yield mock


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


def test_crop_main_files_worker_entry_basic_flow(mock_base_worker, mock_process):
    """Test basic flow of crop_main_files_worker_entry."""
    mock_process.return_value = make_completed_result()

    crop_main_files_worker_entry(job_id=1, user=None)

    mock_process.assert_called_once()

    # Verify final status was updated via after_run()
    final_call = mock_base_worker["update_job_status_with_retry"].call_args
    assert final_call[0][0] == 1
    assert final_call[0][1] == "completed"


def test_crop_main_files_worker_entry_with_user(mock_base_worker, mock_process):
    """Test crop_main_files_worker_entry passes user to CropMainFilesWorker."""
    user = {"username": "testuser"}

    mock_process.return_value = make_completed_result({"total": 5, "processed": 5, "cropped": 5, "uploaded": 5})

    crop_main_files_worker_entry(job_id=1, user=user)

    # Verify the entry point runs and process is called
    mock_process.assert_called_once()

    # Verify final status is updated
    final_call = mock_base_worker["update_job_status_with_retry"].call_args
    assert final_call[0][1] == "completed"


def test_crop_main_files_worker_entry_with_cancel_event(mock_base_worker, mock_process):
    """Test crop_main_files_worker_entry passes cancel_event to CropMainFilesWorker."""
    cancel_event = threading.Event()

    cancelled_result = make_completed_result()
    cancelled_result.status = "cancelled"
    cancelled_result.cancelled_at = datetime.now().isoformat()
    mock_process.return_value = cancelled_result

    crop_main_files_worker_entry(job_id=1, user=None, cancel_event=cancel_event)

    mock_process.assert_called_once()
    # Verify cancelled status is preserved
    final_call = mock_base_worker["update_job_status_with_retry"].call_args
    assert final_call[0][1] == "cancelled"


def test_crop_main_files_worker_entry_handles_exception(mock_base_worker, mock_process):
    """Test that exceptions during processing are handled gracefully."""
    mock_base_worker["save_job_result_by_name"].reset_mock()

    mock_process.side_effect = RuntimeError("Database connection failed")

    crop_main_files_worker_entry(job_id=1, user=None)

    # after_run() saves the final result
    save_calls = mock_base_worker["save_job_result_by_name"].call_args_list
    assert len(save_calls) >= 1

    # Check the last saved result has error details
    last_saved = save_calls[-1][0][1]
    assert last_saved["status"] == "failed"
    assert "Database connection failed" in last_saved["errors"][0]["error"]
    assert last_saved["errors"][0]["error_type"] == "RuntimeError"


def test_crop_main_files_worker_entry_sets_completed_timestamp(mock_base_worker, mock_process):
    """Test that completed_at timestamp is set."""
    mock_base_worker["save_job_result_by_name"].reset_mock()

    mock_process.return_value = make_completed_result()

    crop_main_files_worker_entry(job_id=1, user=None)

    # Verify completed_at was set by after_run()
    save_calls = mock_base_worker["save_job_result_by_name"].call_args_list
    assert len(save_calls) >= 1
    last_saved = save_calls[-1][0][1]
    assert last_saved["completed_at"] is not None
    datetime.fromisoformat(last_saved["completed_at"])


def test_crop_main_files_worker_entry_saves_final_result(mock_base_worker, mock_process):
    """Test that final result is saved."""
    mock_base_worker["save_job_result_by_name"].reset_mock()

    mock_process.return_value = make_completed_result({"total": 3, "processed": 3, "cropped": 3, "skipped": 3})

    crop_main_files_worker_entry(job_id=1, user=None)

    save_calls = mock_base_worker["save_job_result_by_name"].call_args_list
    assert len(save_calls) >= 1
    call_args = save_calls[-1]
    assert call_args[0][0] == "crop_main_files_job_1.json"


def test_crop_main_files_worker_entry_updates_final_status(mock_base_worker, mock_process):
    """Test that final job status is updated."""

    crop_main_files_worker_entry(job_id=1, user=None)

    final_call = mock_base_worker["update_job_status_with_retry"].call_args
    assert final_call[0][0] == 1
    assert final_call[0][1] == "completed"
    assert final_call[0][2] == "crop_main_files_job_1.json"
    assert final_call[1]["job_type"] == "crop_main_files"


def test_crop_main_files_worker_entry_handles_save_failure(mock_base_worker, mock_process):
    """Test that failures to save results are handled gracefully."""
    mock_base_worker["save_job_result_by_name"].side_effect = Exception("Disk full")

    # Should not raise exception
    crop_main_files_worker_entry(job_id=1, user=None)


def test_crop_main_files_worker_entry_handles_status_update_failure(mock_base_worker, mock_process):
    """Test that failures to update status are handled gracefully."""
    mock_base_worker["update_job_status"].side_effect = LookupError("Job not found")

    # Should not raise exception
    crop_main_files_worker_entry(job_id=1, user=None)


def test_crop_main_files_worker_entry_generates_correct_result_file_name(mock_base_worker, mock_process):
    """Test that result file name is generated correctly."""

    crop_main_files_worker_entry(job_id=1, user=None)

    mock_base_worker["generate_result_file_name"].assert_called_once_with(1, "crop_main_files")


def test_crop_main_files_worker_entry_passes_result_file_to_process(mock_base_worker, mock_process):
    """Test that result_file is available on the worker."""
    mock_base_worker["save_job_result_by_name"].reset_mock()

    crop_main_files_worker_entry(job_id=1, user=None)

    # Verify result was saved with correct file name
    save_calls = mock_base_worker["save_job_result_by_name"].call_args_list
    assert len(save_calls) >= 1
    assert save_calls[-1][0][0] == "crop_main_files_job_1.json"


def test_crop_main_files_worker_entry_preserves_cancelled_status(mock_base_worker, mock_process):
    """Test that cancelled status is preserved in final update."""
    cancelled_result = make_completed_result()
    cancelled_result.status = "cancelled"
    cancelled_result.cancelled_at = datetime.now().isoformat()
    cancelled_result.summary.total = 5
    cancelled_result.summary.processed = 2
    cancelled_result.summary.cropped = 2

    mock_process.return_value = cancelled_result

    crop_main_files_worker_entry(job_id=1, user=None)

    final_call = mock_base_worker["update_job_status_with_retry"].call_args
    assert final_call[0][1] == "cancelled"


def test_crop_main_files_worker_entry_preserves_failed_status(mock_base_worker, mock_process):
    """Test that failed status from process is preserved."""
    failed_result = make_completed_result()
    failed_result.status = "failed"
    failed_result.summary.total = 5
    failed_result.summary.failed = 5
    mock_process.return_value = failed_result

    crop_main_files_worker_entry(job_id=1, user=None)

    final_call = mock_base_worker["update_job_status_with_retry"].call_args
    assert final_call[0][1] == "failed"


def test_crop_main_files_worker_entry_different_exception_types(mock_base_worker, mock_process):
    """Test handling of different exception types."""
    exception_types = [
        (ValueError("Invalid value"), "ValueError"),
        (KeyError("Missing key"), "KeyError"),
        (OSError("File not found"), "OSError"),
        (Exception("Generic error"), "Exception"),
    ]

    for exception, expected_type in exception_types:
        mock_base_worker["save_job_result_by_name"].reset_mock()
        mock_base_worker["update_job_status"].reset_mock()

        mock_process.side_effect = exception

        crop_main_files_worker_entry(job_id=1, user=None)

        save_calls = mock_base_worker["save_job_result_by_name"].call_args_list
        assert len(save_calls) >= 1
        last_saved = save_calls[-1][0][1]
        assert last_saved["errors"][0]["error_type"] == expected_type


def test_crop_main_files_worker_entry_upload_files_flag(mock_base_worker, mock_process):
    """Test that upload_files is True in the worker's process method."""

    crop_main_files_worker_entry(job_id=1, user=None)

    mock_process.assert_called_once()


def test_crop_main_files_worker_entry_multiple_jobs(mock_base_worker, mock_process):
    """Test running multiple jobs with different IDs."""

    crop_main_files_worker_entry(job_id=1, user=None)
    crop_main_files_worker_entry(job_id=2, user=None)
    crop_main_files_worker_entry(job_id=3, user=None)

    assert mock_base_worker["generate_result_file_name"].call_count == 3
    calls = mock_base_worker["generate_result_file_name"].call_args_list
    assert calls[0][0] == (1, "crop_main_files")
    assert calls[1][0] == (2, "crop_main_files")
    assert calls[2][0] == (3, "crop_main_files")


def test_crop_main_files_worker_entry_exception_includes_traceback_in_logs(mock_base_worker, mock_process):
    """Test that exceptions are logged with full traceback."""
    with patch("src.main_app.jobs_workers.base_worker.logger") as mock_logger:
        mock_process.side_effect = RuntimeError("Test error")

        crop_main_files_worker_entry(job_id=1, user=None)

    # handle_error() calls logger.exception()
    mock_logger.exception.assert_called_once()


def test_crop_main_files_worker_entry_completed_status_default(mock_base_worker, mock_process):
    """Test that default status is completed when no other status is set."""
    mock_process.return_value = make_completed_result()

    crop_main_files_worker_entry(job_id=1, user=None)

    final_call = mock_base_worker["update_job_status_with_retry"].call_args
    assert final_call[0][1] == "completed"


def test_crop_main_files_worker_entry_accepts_args_keyword_param(mock_base_worker, mock_process):
    """Test that crop_main_files_worker_entry accepts args= keyword-only param (unified signature)."""

    # Should not raise TypeError
    crop_main_files_worker_entry(job_id=1, user=None, args={"some_key": "value"})

    mock_process.assert_called_once()


def test_crop_main_files_worker_entry_args_defaults_to_none(mock_base_worker, mock_process):
    """Test that args defaults to None and entry point works without it."""

    crop_main_files_worker_entry(job_id=2, user=None)

    mock_process.assert_called_once()


def test_crop_main_files_worker_entry_maps_crop_newest_upload_limit(mock_instance_class, mock_base_worker):
    """Test that upload_limit is mapped to upload_limit in args."""
    crop_main_files_worker_entry(job_id=1, user=None, args={"upload_limit": 3})

    call_args = mock_instance_class.call_args
    passed_args = call_args[0][3] if len(call_args[0]) > 3 else call_args.kwargs.get("args")
    assert passed_args is not None
    assert passed_args["upload_limit"] == 3


def test_crop_main_files_worker_entry_does_not_map_when_key_absent(mock_instance_class, mock_base_worker):
    """Test that args are passed unchanged when upload_limit is absent."""

    crop_main_files_worker_entry(job_id=1, user=None, args={"other_key": "value"})

    call_args = mock_instance_class.call_args
    passed_args = call_args[0][3] if len(call_args[0]) > 3 else call_args.kwargs.get("args")
    assert "upload_limit" not in passed_args


def test_crop_main_files_worker_entry_does_not_modify_args_when_none(mock_instance_class, mock_base_worker):
    """Test that entry point works correctly when args is None."""
    crop_main_files_worker_entry(job_id=1, user=None, args=None)

    call_args = mock_instance_class.call_args
    passed_args = call_args[0][3] if len(call_args[0]) > 3 else call_args.kwargs.get("args")
    assert passed_args is None
