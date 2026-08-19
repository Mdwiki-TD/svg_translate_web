"""Unit tests for download_main_files runner module."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from src.main_app.api_services.files_service import DownloadAndSaveData
from src.main_app.database.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.download_main_files import DownloadMainFilesWorker
from src.main_app.jobs_workers.objects import JobsRunner


@dataclass
class MockServices:
    list: MagicMock
    download_and_save: MagicMock
    generate_main_files_zip: MagicMock
    create_commons_session: MagicMock
    before_run: MagicMock


@pytest.fixture
def mock_path(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    _mock_class = MagicMock()
    _mock_instance = MagicMock()
    _mock_class.return_value = _mock_instance
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.Path",
        _mock_class,
    )
    return _mock_class


@pytest.fixture
def mock_download_main_services(monkeypatch: pytest.MonkeyPatch, mock_before_run) -> MockServices:
    mock_list_templates = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.TemplateService.list",
        mock_list_templates,
    )

    mock_download_and_save = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.FilesService.download_and_save",
        mock_download_and_save,
    )

    mock_generate_main_files_zip = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.generate_main_files_zip",
        mock_generate_main_files_zip,
    )

    mock_create_commons_session = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.create_commons_session",
        mock_create_commons_session,
    )

    return MockServices(
        list=mock_list_templates,
        download_and_save=mock_download_and_save,
        generate_main_files_zip=mock_generate_main_files_zip,
        create_commons_session=mock_create_commons_session,
        before_run=mock_before_run,
    )


def test_download_main_files_with_no_templates(
    mock_path, mock_base_worker, mock_download_main_services: MockServices, tmp_path
):
    """Test processing when no templates have main files."""
    mock_download_main_services.list.return_value = []
    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    worker.run()

    assert mock_base_worker["save_job_result_by_name"].called
    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 0


def test_download_main_files_skips_templates_without_main_file(
    mock_path, mock_base_worker, mock_download_main_services: MockServices, tmp_path
):
    """Test that templates without main files are skipped during loading."""
    templates = [
        TemplateRecord(id=1, title="T1", main_file=None),
        TemplateRecord(id=2, title="T2", main_file="file2.svg"),
    ]
    mock_download_main_services.list.return_value = templates
    mock_download_main_services.download_and_save.return_value = DownloadAndSaveData(result="success", path="file2.svg")

    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    worker.run()

    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 1
    assert mock_download_main_services.download_and_save.call_count == 1


def test_download_main_files_downloads_template_with_main_file(
    mock_path, mock_base_worker, mock_download_main_services: MockServices, tmp_path
):
    """Test successful download workflow."""
    templates = [TemplateRecord(id=1, title="T1", main_file="file1.svg")]
    mock_download_main_services.list.return_value = templates
    mock_download_main_services.download_and_save.return_value = DownloadAndSaveData(
        result="success",
        path="file1.svg",
        error=None,
        size_bytes=100,
    )
    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    worker.run()

    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["files_downloaded"]) == 1
    assert result_dict["files_downloaded"][0]["filename"] == "file1.svg"


def test_download_main_files_handles_download_failure(
    mock_path, mock_base_worker, mock_download_main_services: MockServices, tmp_path
):
    """Test handled failure during file download."""
    templates = [TemplateRecord(id=1, title="T1", main_file="file1.svg")]
    mock_download_main_services.list.return_value = templates
    mock_download_main_services.download_and_save.return_value = DownloadAndSaveData(result="failed", error="NotFound")

    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    worker.run()

    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["files_failed"]) == 1
    assert result_dict["files_failed"][0]["error"] == "NotFound"


def test_download_main_files_handles_exception(
    mock_path, mock_base_worker, mock_download_main_services: MockServices, tmp_path
):
    """Test unhandled exception during processing."""
    templates = [TemplateRecord(id=1, title="T1", main_file="file1.svg")]
    mock_download_main_services.list.return_value = templates
    mock_download_main_services.download_and_save.side_effect = Exception("Fatal error")

    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    worker.run()

    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["files_failed"]) == 1
    assert "Fatal error" in result_dict["files_failed"][0]["error"]


def test_download_main_files_processes_multiple_templates(
    mock_path, mock_base_worker, mock_download_main_services: MockServices, tmp_path
):
    """Test multiple templates with mixed results."""
    templates = [
        TemplateRecord(id=1, title="T1", main_file="file1.svg"),
        TemplateRecord(id=2, title="T2", main_file="file2.svg"),
    ]
    mock_download_main_services.list.return_value = templates

    def download_side_effect(title, *args, **kwargs):
        if title == "file1.svg":
            return DownloadAndSaveData(result="success", path="file1.svg")
        return DownloadAndSaveData(result="failed", error="Fail")

    mock_download_main_services.download_and_save.side_effect = download_side_effect

    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    worker.run()

    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert len(result_dict["files_downloaded"]) == 1
    assert len(result_dict["files_failed"]) == 1


def test_download_main_files_respects_cancellation(
    mock_path, mock_base_worker, mock_download_main_services: MockServices, tmp_path
):
    """Test cancellation after first template."""
    templates = [
        TemplateRecord(id=1, title="T1", main_file="file1.svg"),
        TemplateRecord(id=2, title="T2", main_file="file2.svg"),
    ]
    mock_download_main_services.list.return_value = templates
    mock_download_main_services.download_and_save.return_value = DownloadAndSaveData(result="success")

    cancel_event = threading.Event()

    def download_with_cancel(*args, **kwargs):
        cancel_event.set()
        return DownloadAndSaveData(result="success", path="file.svg")

    mock_download_main_services.download_and_save.side_effect = download_with_cancel

    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
            cancel_event=cancel_event,
        )
    )
    worker.run()

    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["processed"] == 1
    assert result_dict["status"] == "cancelled"


def test_download_main_files_handles_file_with_file_prefix(
    mock_path, mock_base_worker, mock_download_main_services: MockServices, tmp_path
):
    """Test that 'File:' prefix is handled correctly."""
    templates = [TemplateRecord(id=1, title="T1", main_file="File:Example.svg")]
    mock_download_main_services.list.return_value = templates
    mock_download_main_services.download_and_save.return_value = DownloadAndSaveData(
        result="success", path="Example.svg"
    )

    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    worker.run()

    _call = mock_download_main_services.download_and_save.call_args[1]
    passed_filename = _call["title"]
    assert passed_filename == "File:Example.svg"


def test_download_main_files_checks_if_file_exists(
    mock_path, mock_base_worker, mock_download_main_services: MockServices, tmp_path
):
    """Test worker handles existing files (overwrites by design)."""
    templates = [TemplateRecord(id=1, title="T1", main_file="exists.svg")]
    mock_download_main_services.list.return_value = templates
    mock_download_main_services.download_and_save.return_value = DownloadAndSaveData(
        result="success", path="exists.svg"
    )

    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    worker.run()
    assert mock_download_main_services.download_and_save.called


def test_download_main_files_fatal_error_handling(
    mock_path, mock_base_worker, mock_download_main_services: MockServices, tmp_path
):
    """Test workflow when an error occurs but partial results are saved."""
    mock_download_main_services.list.side_effect = Exception("DB Fail")

    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    worker.run()

    mock_base_worker["update_job_status_with_retry"].assert_called_with(
        1, "failed", "download_main_files_job_1.json", job_type="download_main_files"
    )


def test_download_main_files_saves_progress_periodically(
    mock_path, mock_base_worker, mock_download_main_services: MockServices, tmp_path
):
    """Test that save_progress is called."""
    templates = [TemplateRecord(id=i, title=f"T{i}", main_file=f"f{i}.svg") for i in range(1, 5)]
    mock_download_main_services.list.return_value = templates
    mock_download_main_services.download_and_save.return_value = DownloadAndSaveData(
        result="success",
        path=None,
        error=None,
    )

    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    worker.run()

    assert mock_base_worker["save_job_result_by_name"].call_count >= 2


def test_download_main_files_creates_output_directory(
    mock_path, mock_base_worker, mock_download_main_services: MockServices, tmp_path
):
    """Test that the output directory is created if missing."""
    mock_download_main_services.list.return_value = []
    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    worker.run()

    mock_path.return_value.mkdir.assert_called()


def test_download_main_files_generates_zip_on_completion(
    mock_path, mock_base_worker, mock_download_main_services: MockServices, tmp_path
):
    """Test that zip generation is triggered."""
    mock_download_main_services.list.return_value = []
    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    worker.run()

    mock_download_main_services.generate_main_files_zip.assert_called_once()


def test_download_main_files_no_zip_on_failure(mock_path, mock_download_main_services: MockServices, tmp_path):
    """Test that zip generation is skipped if job is failed/cancelled."""
    mock_download_main_services.list.side_effect = Exception("Fail")

    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    worker.run()

    mock_download_main_services.generate_main_files_zip.assert_not_called()


def test_download_main_files_for_templates_accepts_args_keyword_param(
    mock_path, mock_download_main_services: MockServices
):
    """Test entry point unified signature."""
    mock_download_main_services.list.return_value = []
    worker = DownloadMainFilesWorker(
        JobsRunner(
            job_id=1,
            user={},
            args={"some": "val"},
        )
    )
    worker.run()


def test_download_main_files_for_templates_args_defaults_to_none(mock_path, mock_download_main_services: MockServices):
    """Test entry point works with default args."""
    mock_download_main_services.list.return_value = []

    worker = DownloadMainFilesWorker(JobsRunner(job_id=99, user={}))
    worker.run()


class TestDownloadMainFilesWorkerApplyLimits:
    def test_apply_limits_with_limit_set(self):
        templates = [TemplateRecord(id=1, title="T1", main_file="f1"), TemplateRecord(id=2, title="T2", main_file="f2")]
        w = DownloadMainFilesWorker(
            JobsRunner(
                job_id=1,
                user={},
                args={"limit_items": 1},
            )
        )
        result = w._apply_limits(templates)
        assert len(result) == 1

    def test_apply_limits_with_zero_limit(self):
        templates = [TemplateRecord(id=1, title="T1", main_file="f1")]
        w = DownloadMainFilesWorker(
            JobsRunner(
                job_id=1,
                user={},
                args={"limit_items": 0},
            )
        )
        result = w._apply_limits(templates)
        assert len(result) == 1
