"""Unit tests for crop_main_files.worker module."""

from __future__ import annotations

import threading
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.jobs_workers.crop_main_files import worker


@pytest.fixture
def mock_services(monkeypatch: pytest.MonkeyPatch):
    """Mock the services used by worker module."""

    # Mock jobs_service
    mock_update_job_status = MagicMock()
    mock_save_job_result = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.worker.jobs_service.update_job_status",
        mock_update_job_status
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.worker.jobs_service.save_job_result_by_name",
        mock_save_job_result
    )

    # Mock generate_result_file_name
    mock_generate_result_file_name = MagicMock(
        side_effect=lambda job_id, job_type: f"{job_type}_job_{job_id}.json"
    )
    monkeypatch.setattr(
        "src.main_app.jobs_workers.crop_main_files.worker.generate_result_file_name",
        mock_generate_result_file_name
    )

    return {
        "update_job_status": mock_update_job_status,
        "save_job_result_by_name": mock_save_job_result,
        "generate_result_file_name": mock_generate_result_file_name,
    }


def test_crop_main_files_for_templates_basic_flow(mock_services):
    """Test basic flow of crop_main_files_for_templates."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "completed",
            "summary": {
                "total": 10,
                "processed": 10,
                "cropped": 8,
                "uploaded": 0,
                "failed": 2,
                "skipped": 0,
            },
            "files_processed": [],
        }

        worker.crop_main_files_for_templates(1)

    # Verify process_crops was called
    mock_process.assert_called_once()
    call_args = mock_process.call_args

    assert call_args[0][0] == 1  # job_id
    call_kwargs = call_args.kwargs if hasattr(call_args, 'kwargs') else call_args[1] if len(call_args) > 1 else {}
    assert call_kwargs.get("user") is None
    assert call_kwargs.get("cancel_event") is None
    assert call_kwargs.get("upload_files") is False


def test_crop_main_files_for_templates_initializes_result(mock_services):
    """Test that result structure is properly initialized."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        def capture_result(job_id, result, result_file, user, cancel_event=None, upload_files=False):
            # Verify the initial result structure
            assert result["status"] == "pending"
            assert "started_at" in result
            assert result["completed_at"] is None
            assert result["cancelled_at"] is None
            assert result["summary"]["total"] == 0
            assert result["summary"]["processed"] == 0
            assert result["summary"]["cropped"] == 0
            assert result["summary"]["uploaded"] == 0
            assert result["summary"]["failed"] == 0
            assert result["summary"]["skipped"] == 0
            assert result["files_processed"] == []
            return result

        mock_process.side_effect = capture_result

        worker.crop_main_files_for_templates(1)


def test_crop_main_files_for_templates_with_user(mock_services):
    """Test crop_main_files_for_templates with user authentication."""
    user = {"username": "testuser"}

    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "completed",
            "summary": {
                "total": 5,
                "processed": 5,
                "cropped": 5,
                "uploaded": 5,
                "failed": 0,
                "skipped": 0,
            },
            "files_processed": [],
        }

        worker.crop_main_files_for_templates(1, user=user)

    # Verify user was passed to process_crops
    call_args = mock_process.call_args
    # user is the 4th positional argument (job_id, result, result_file, user)
    assert call_args[0][3] is user


def test_crop_main_files_for_templates_with_cancel_event(mock_services):
    """Test crop_main_files_for_templates with cancel event."""
    cancel_event = threading.Event()

    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "cancelled",
            "summary": {
                "total": 5,
                "processed": 2,
                "cropped": 2,
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
            },
            "files_processed": [],
        }

        worker.crop_main_files_for_templates(1, cancel_event=cancel_event)

    # Verify cancel_event was passed to process_crops
    call_args = mock_process.call_args
    assert call_args[1]["cancel_event"] is cancel_event


def test_crop_main_files_for_templates_handles_exception(mock_services):
    """Test that exceptions during processing are handled gracefully."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.side_effect = RuntimeError("Database connection failed")

        worker.crop_main_files_for_templates(1)

    # Verify final result was saved with error details
    final_result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert final_result["status"] == "failed"
    assert "Database connection failed" in final_result["error"]
    assert final_result["error_type"] == "RuntimeError"


def test_crop_main_files_for_templates_sets_completed_timestamp(mock_services):
    """Test that completed_at timestamp is set."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "completed",
            "summary": {
                "total": 0,
                "processed": 0,
                "cropped": 0,
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
            },
            "files_processed": [],
        }

        worker.crop_main_files_for_templates(1)

    # Verify completed_at was set
    final_result = mock_services["save_job_result_by_name"].call_args[0][1]
    assert final_result["completed_at"] is not None
    # Verify it's a valid ISO format timestamp
    datetime.fromisoformat(final_result["completed_at"])


def test_crop_main_files_for_templates_saves_final_result(mock_services):
    """Test that final result is saved."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "completed",
            "summary": {
                "total": 3,
                "processed": 3,
                "cropped": 3,
                "uploaded": 0,
                "failed": 0,
                "skipped": 3,
            },
            "files_processed": [],
        }

        worker.crop_main_files_for_templates(1)

    # Verify save was called
    mock_services["save_job_result_by_name"].assert_called()
    call_args = mock_services["save_job_result_by_name"].call_args
    assert call_args[0][0] == "crop_main_files_job_1.json"


def test_crop_main_files_for_templates_updates_final_status(mock_services):
    """Test that final job status is updated."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "completed",
            "summary": {
                "total": 0,
                "processed": 0,
                "cropped": 0,
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
            },
            "files_processed": [],
        }

        worker.crop_main_files_for_templates(1)

    # Verify final status update was called
    final_call = mock_services["update_job_status"].call_args
    assert final_call[0][0] == 1  # job_id
    assert final_call[0][1] == "completed"  # status
    assert final_call[0][2] == "crop_main_files_job_1.json"  # result_file
    assert final_call[1]["job_type"] == "crop_main_files"


def test_crop_main_files_for_templates_handles_save_failure(mock_services):
    """Test that failures to save results are handled gracefully."""
    mock_services["save_job_result_by_name"].side_effect = Exception("Disk full")

    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "completed",
            "summary": {
                "total": 0,
                "processed": 0,
                "cropped": 0,
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
            },
            "files_processed": [],
        }

        # Should not raise exception
        worker.crop_main_files_for_templates(1)


def test_crop_main_files_for_templates_handles_status_update_failure(mock_services):
    """Test that failures to update status are handled gracefully."""
    mock_services["update_job_status"].side_effect = LookupError("Job not found")

    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "completed",
            "summary": {
                "total": 0,
                "processed": 0,
                "cropped": 0,
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
            },
            "files_processed": [],
        }

        # Should not raise exception
        worker.crop_main_files_for_templates(1)


def test_crop_main_files_for_templates_generates_correct_result_file_name(mock_services):
    """Test that result file name is generated correctly."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "completed",
            "summary": {
                "total": 0,
                "processed": 0,
                "cropped": 0,
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
            },
            "files_processed": [],
        }

        worker.crop_main_files_for_templates(1)

    # Verify generate_result_file_name was called correctly
    mock_services["generate_result_file_name"].assert_called_once_with(1, "crop_main_files")


def test_crop_main_files_for_templates_passes_result_file_to_process(mock_services):
    """Test that result_file is passed to process_crops."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "completed",
            "summary": {
                "total": 0,
                "processed": 0,
                "cropped": 0,
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
            },
            "files_processed": [],
        }

        worker.crop_main_files_for_templates(1)

    # Verify result_file was passed to process_crops
    call_args = mock_process.call_args
    assert call_args[0][2] == "crop_main_files_job_1.json"


def test_crop_main_files_for_templates_preserves_cancelled_status(mock_services):
    """Test that cancelled status is preserved in final update."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat(),
            "summary": {
                "total": 5,
                "processed": 2,
                "cropped": 2,
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
            },
            "files_processed": [],
        }

        worker.crop_main_files_for_templates(1)

    # Verify final status is cancelled
    final_call = mock_services["update_job_status"].call_args
    assert final_call[0][1] == "cancelled"


def test_crop_main_files_for_templates_preserves_failed_status(mock_services):
    """Test that failed status from process_crops is preserved."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "failed",
            "error": "Some processing error",
            "summary": {
                "total": 5,
                "processed": 1,
                "cropped": 0,
                "uploaded": 0,
                "failed": 5,
                "skipped": 0,
            },
            "files_processed": [],
        }

        worker.crop_main_files_for_templates(1)

    # Verify final status is failed
    final_call = mock_services["update_job_status"].call_args
    assert final_call[0][1] == "failed"


def test_crop_main_files_for_templates_different_exception_types(mock_services):
    """Test handling of different exception types."""
    exception_types = [
        (ValueError("Invalid value"), "ValueError"),
        (KeyError("Missing key"), "KeyError"),
        (OSError("File not found"), "OSError"),
        (Exception("Generic error"), "Exception"),
    ]

    for exception, expected_type in exception_types:
        mock_services["save_job_result_by_name"].reset_mock()

        with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
            mock_process.side_effect = exception

            worker.crop_main_files_for_templates(1)

        # Verify error_type is set correctly
        final_result = mock_services["save_job_result_by_name"].call_args[0][1]
        assert final_result["error_type"] == expected_type


def test_crop_main_files_for_templates_upload_files_flag(mock_services):
    """Test that upload_files flag is always False."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "completed",
            "summary": {
                "total": 0,
                "processed": 0,
                "cropped": 0,
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
            },
            "files_processed": [],
        }

        worker.crop_main_files_for_templates(1)

    # Verify upload_files is False
    call_args = mock_process.call_args
    assert call_args[1]["upload_files"] is False


def test_crop_main_files_for_templates_multiple_jobs(mock_services):
    """Test running multiple jobs with different IDs."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        mock_process.return_value = {
            "status": "completed",
            "summary": {
                "total": 0,
                "processed": 0,
                "cropped": 0,
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
            },
            "files_processed": [],
        }

        worker.crop_main_files_for_templates(1)
        worker.crop_main_files_for_templates(2)
        worker.crop_main_files_for_templates(3)

    # Verify correct result file names were generated
    assert mock_services["generate_result_file_name"].call_count == 3
    calls = mock_services["generate_result_file_name"].call_args_list
    assert calls[0][0] == (1, "crop_main_files")
    assert calls[1][0] == (2, "crop_main_files")
    assert calls[2][0] == (3, "crop_main_files")


def test_crop_main_files_for_templates_started_at_timestamp(mock_services):
    """Test that started_at timestamp is set correctly."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        def capture_result(job_id, result, result_file, user, cancel_event=None, upload_files=False):
            # Verify started_at is a valid timestamp
            assert "started_at" in result
            datetime.fromisoformat(result["started_at"])
            return result

        mock_process.side_effect = capture_result

        worker.crop_main_files_for_templates(1)


def test_crop_main_files_for_templates_exception_includes_traceback_in_logs(mock_services):
    """Test that exceptions are logged with full traceback."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process, \
         patch('src.main_app.jobs_workers.crop_main_files.worker.logger') as mock_logger:

        mock_process.side_effect = RuntimeError("Test error")

        worker.crop_main_files_for_templates(1)

    # Verify logger.exception was called (logs with traceback)
    mock_logger.exception.assert_called_once()
    assert "Test error" in str(mock_logger.exception.call_args) or "Error during crop processing" in str(mock_logger.exception.call_args)


def test_crop_main_files_for_templates_completed_status_default(mock_services):
    """Test that default status is completed when no other status is set."""
    with patch('src.main_app.jobs_workers.crop_main_files.worker.process_crops') as mock_process:
        # Return result without explicit status
        mock_process.return_value = {
            "summary": {
                "total": 0,
                "processed": 0,
                "cropped": 0,
                "uploaded": 0,
                "failed": 0,
                "skipped": 0,
            },
            "files_processed": [],
        }

        worker.crop_main_files_for_templates(1)

    # Verify final status defaults to completed
    final_call = mock_services["update_job_status"].call_args
    assert final_call[0][1] == "completed"