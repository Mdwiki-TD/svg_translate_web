"""Unit tests for download_main_files runner module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.download_main_files import runner


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


def test_download_main_files_with_no_templates(mock_base_worker, mock_services, tmp_path):
    """Test processing when no templates have main files."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        mock_services["list_templates"].return_value = []
        runner.download_main_files_for_templates(job_id=1, user=None)

        assert mock_base_worker["save_job_result_by_name"].called
        result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["total"] == 0


def test_download_main_files_skips_templates_without_main_file(mock_base_worker, mock_services, tmp_path):
    """Test that templates without main files are skipped during loading."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        templates = [
            TemplateRecord(id=1, title="T1", main_file=None),
            TemplateRecord(id=2, title="T2", main_file="file2.svg"),
        ]
        mock_services["list_templates"].return_value = templates
        mock_services["download_file_from_commons"].return_value = {"success": True, "path": "file2.svg"}

        runner.download_main_files_for_templates(job_id=1, user=None)

        result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["total"] == 1
        assert mock_services["download_file_from_commons"].call_count == 1


def test_download_main_files_downloads_template_with_main_file(mock_base_worker, mock_services, tmp_path):
    """Test successful download workflow."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        templates = [TemplateRecord(id=1, title="T1", main_file="file1.svg")]
        mock_services["list_templates"].return_value = templates
        mock_services["download_file_from_commons"].return_value = {
            "success": True,
            "path": "file1.svg",
            "size_bytes": 100,
        }

        runner.download_main_files_for_templates(job_id=1, user=None)

        result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["success"] == 1
        assert len(result_dict["files_downloaded"]) == 1
        assert result_dict["files_downloaded"][0]["filename"] == "file1.svg"


def test_download_main_files_handles_download_failure(mock_base_worker, mock_services, tmp_path):
    """Test handled failure during file download."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        templates = [TemplateRecord(id=1, title="T1", main_file="file1.svg")]
        mock_services["list_templates"].return_value = templates
        mock_services["download_file_from_commons"].return_value = {"success": False, "error": "NotFound"}

        runner.download_main_files_for_templates(job_id=1, user=None)

        result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["failed"] == 1
        assert len(result_dict["files_failed"]) == 1
        assert result_dict["files_failed"][0]["reason"] == "NotFound"


def test_download_main_files_handles_exception(mock_base_worker, mock_services, tmp_path):
    """Test unhandled exception during processing."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        templates = [TemplateRecord(id=1, title="T1", main_file="file1.svg")]
        mock_services["list_templates"].return_value = templates
        mock_services["download_file_from_commons"].side_effect = Exception("Fatal error")

        runner.download_main_files_for_templates(job_id=1, user=None)

        result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["failed"] == 1
        assert "Fatal error" in result_dict["files_failed"][0]["reason"]


def test_download_main_files_processes_multiple_templates(mock_base_worker, mock_services, tmp_path):
    """Test multiple templates with mixed results."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        templates = [
            TemplateRecord(id=1, title="T1", main_file="file1.svg"),
            TemplateRecord(id=2, title="T2", main_file="file2.svg"),
        ]
        mock_services["list_templates"].return_value = templates

        def download_side_effect(filename, *args, **kwargs):
            if filename == "file1.svg":
                return {"success": True, "path": "file1.svg"}
            return {"success": False, "error": "Fail"}

        mock_services["download_file_from_commons"].side_effect = download_side_effect

        runner.download_main_files_for_templates(job_id=1, user=None)

        result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["success"] == 1
        assert result_dict["summary"]["failed"] == 1


def test_download_main_files_respects_cancellation(mock_base_worker, mock_services, tmp_path):
    """Test cancellation after first template."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        templates = [
            TemplateRecord(id=1, title="T1", main_file="file1.svg"),
            TemplateRecord(id=2, title="T2", main_file="file2.svg"),
        ]
        mock_services["list_templates"].return_value = templates
        mock_services["download_file_from_commons"].return_value = {"success": True}

        cancel_event = threading.Event()

        def download_with_cancel(*args, **kwargs):
            cancel_event.set()
            return {"success": True, "path": "file.svg"}

        mock_services["download_file_from_commons"].side_effect = download_with_cancel

        runner.download_main_files_for_templates(job_id=1, user=None, cancel_event=cancel_event)

        result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
        assert result_dict["summary"]["processed"] == 1
        assert result_dict["status"] == "cancelled"


def test_download_main_files_handles_file_with_file_prefix(mock_services, tmp_path):
    """Test that 'File:' prefix is handled correctly."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        templates = [TemplateRecord(id=1, title="T1", main_file="File:Example.svg")]
        mock_services["list_templates"].return_value = templates
        mock_services["download_file_from_commons"].return_value = {"success": True, "path": "Example.svg"}

        runner.download_main_files_for_templates(job_id=1, user=None)

        _call = mock_services["download_file_from_commons"].call_args[1]
        passed_filename = _call["filename"]
        assert passed_filename == "Example.svg"

def test_download_main_files_checks_if_file_exists(mock_services, tmp_path):
    """Test worker handles existing files (overwrites by design)."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        templates = [TemplateRecord(id=1, title="T1", main_file="exists.svg")]
        mock_services["list_templates"].return_value = templates
        mock_services["download_file_from_commons"].return_value = {"success": True, "path": "exists.svg"}

        runner.download_main_files_for_templates(job_id=1, user=None)
        assert mock_services["download_file_from_commons"].called


def test_download_main_files_fatal_error_handling(mock_base_worker, mock_services, tmp_path):
    """Test workflow when an error occurs but partial results are saved."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        mock_services["list_templates"].side_effect = Exception("DB Fail")

        runner.download_main_files_for_templates(job_id=1, user=None)

        mock_base_worker["update_job_status_with_retry"].assert_called_with(
            1, "failed", "download_main_files_job_1.json", job_type="download_main_files"
        )


def test_download_main_files_saves_progress_periodically(mock_base_worker, mock_services, tmp_path):
    """Test that save_progress is called."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        templates = [TemplateRecord(id=i, title=f"T{i}", main_file=f"f{i}.svg") for i in range(1, 5)]
        mock_services["list_templates"].return_value = templates
        mock_services["download_file_from_commons"].return_value = {"success": True}

        runner.download_main_files_for_templates(job_id=1, user=None)

        assert mock_base_worker["save_job_result_by_name"].call_count >= 2


def test_download_main_files_creates_output_directory(mock_services, tmp_path):
    """Test that the output directory is created if missing."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        mock_services["list_templates"].return_value = []
        runner.download_main_files_for_templates(job_id=1, user=None)

        mock_instance.mkdir.assert_called()


def test_download_main_files_generates_zip_on_completion(mock_services, tmp_path):
    """Test that zip generation is triggered."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        mock_services["list_templates"].return_value = []
        runner.download_main_files_for_templates(job_id=1, user=None)

        mock_services["generate_main_files_zip"].assert_called_once()


def test_download_main_files_no_zip_on_failure(mock_services, tmp_path):
    """Test that zip generation is skipped if job is failed/cancelled."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_instance = MagicMock()
        mock_path.return_value = mock_instance

        mock_services["list_templates"].side_effect = Exception("Fail")

        runner.download_main_files_for_templates(job_id=1, user=None)

    mock_services["generate_main_files_zip"].assert_not_called()


def test_download_main_files_for_templates_accepts_args_keyword_param(mock_services):
    """Test entry point unified signature."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_path.return_value = MagicMock()
        mock_services["list_templates"].return_value = []
        runner.download_main_files_for_templates(job_id=1, user=None, args={"some": "val"})


def test_download_main_files_for_templates_args_defaults_to_none(mock_services):
    """Test entry point works with default args."""
    with patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path") as mock_path:
        mock_path.return_value = MagicMock()
        mock_services["list_templates"].return_value = []
        runner.download_main_files_for_templates(job_id=99, user=None)


def test_entry_point_maps_limit_items(mock_services):
    """Test that limit_items is mapped."""
    mock_services["list_templates"].return_value = []
    with patch(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner.DownloadMainFilesWorker"
    ) as MockWorker:
        mock_instance = MagicMock()
        MockWorker.return_value = mock_instance

        runner.download_main_files_for_templates(job_id=1, user=None, args={"limit_items": 123})

        call_args = MockWorker.call_args
        passed_args = call_args[0][3] if len(call_args[0]) > 3 else call_args.kwargs.get("args")
        assert isinstance(passed_args, dict)
        assert passed_args.get("limit_items") == 123
