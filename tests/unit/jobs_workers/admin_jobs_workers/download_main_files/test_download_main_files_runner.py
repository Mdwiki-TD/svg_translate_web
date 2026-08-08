"""Unit tests for download_main_files runner module."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.db.models import TemplateRecord
from src.main_app.jobs_workers.admin_jobs_workers.download_main_files import runner
from src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner import (
    MAIN_FILES_ZIP_NAME,
    create_main_files_zip,
)
from src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner import (
    download_main_files_for_templates as _original_download_entry,
)
from src.main_app.jobs_workers.objects import JobsRunner


def download_main_files_for_templates(job_id, user, cancel_event=None, args=None, form_data=None):
    data = JobsRunner(job_id=job_id, user=user, cancel_event=cancel_event, args=args, form_data=form_data)
    return _original_download_entry(data)


runner.download_main_files_for_templates = download_main_files_for_templates


@dataclass
class MockServices:
    list: MagicMock
    download_file_from_commons: MagicMock
    generate_main_files_zip: MagicMock
    create_commons_session: MagicMock
    download_commons_file_core: MagicMock
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
def mock_services(monkeypatch: pytest.MonkeyPatch, mock_before_run) -> MockServices:
    mock_list_templates = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.TemplateService.list",
        mock_list_templates,
    )

    mock_download_file_from_commons = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.worker.download_file_from_commons",
        mock_download_file_from_commons,
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

    mock_download_commons_file_core: MagicMock = MagicMock(return_value=b"svg-content")
    monkeypatch.setattr(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.download_helper.download_commons_file_core",
        mock_download_commons_file_core,
    )

    return MockServices(
        list=mock_list_templates,
        download_file_from_commons=mock_download_file_from_commons,
        generate_main_files_zip=mock_generate_main_files_zip,
        create_commons_session=mock_create_commons_session,
        download_commons_file_core=mock_download_commons_file_core,
        before_run=mock_before_run,
    )


def test_download_main_files_with_no_templates(mock_path, mock_base_worker, mock_services: MockServices, tmp_path):
    """Test processing when no templates have main files."""
    mock_services.list.return_value = []
    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
        )
    )

    assert mock_base_worker["save_job_result_by_name"].called
    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 0


def test_download_main_files_skips_templates_without_main_file(
    mock_path, mock_base_worker, mock_services: MockServices, tmp_path
):
    """Test that templates without main files are skipped during loading."""
    templates = [
        TemplateRecord(id=1, title="T1", main_file=None),
        TemplateRecord(id=2, title="T2", main_file="file2.svg"),
    ]
    mock_services.list.return_value = templates
    mock_services.download_file_from_commons.return_value = {"success": True, "path": "file2.svg"}

    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
        )
    )

    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["total"] == 1
    assert mock_services.download_file_from_commons.call_count == 1


def test_download_main_files_downloads_template_with_main_file(
    mock_path, mock_base_worker, mock_services: MockServices, tmp_path
):
    """Test successful download workflow."""
    templates = [TemplateRecord(id=1, title="T1", main_file="file1.svg")]
    mock_services.list.return_value = templates
    mock_services.download_file_from_commons.return_value = {
        "success": True,
        "path": "file1.svg",
        "size_bytes": 100,
    }

    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
        )
    )

    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["success"] == 1
    assert len(result_dict["files_downloaded"]) == 1
    assert result_dict["files_downloaded"][0]["filename"] == "file1.svg"


def test_download_main_files_handles_download_failure(
    mock_path, mock_base_worker, mock_services: MockServices, tmp_path
):
    """Test handled failure during file download."""
    templates = [TemplateRecord(id=1, title="T1", main_file="file1.svg")]
    mock_services.list.return_value = templates
    mock_services.download_file_from_commons.return_value = {"success": False, "error": "NotFound"}

    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
        )
    )

    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["failed"] == 1
    assert len(result_dict["files_failed"]) == 1
    assert result_dict["files_failed"][0]["reason"] == "NotFound"


def test_download_main_files_handles_exception(mock_path, mock_base_worker, mock_services: MockServices, tmp_path):
    """Test unhandled exception during processing."""
    templates = [TemplateRecord(id=1, title="T1", main_file="file1.svg")]
    mock_services.list.return_value = templates
    mock_services.download_file_from_commons.side_effect = Exception("Fatal error")

    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
        )
    )

    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["failed"] == 1
    assert "Fatal error" in result_dict["files_failed"][0]["reason"]


def test_download_main_files_processes_multiple_templates(
    mock_path, mock_base_worker, mock_services: MockServices, tmp_path
):
    """Test multiple templates with mixed results."""
    templates = [
        TemplateRecord(id=1, title="T1", main_file="file1.svg"),
        TemplateRecord(id=2, title="T2", main_file="file2.svg"),
    ]
    mock_services.list.return_value = templates

    def download_side_effect(filename, *args, **kwargs):
        if filename == "file1.svg":
            return {"success": True, "path": "file1.svg"}
        return {"success": False, "error": "Fail"}

    mock_services.download_file_from_commons.side_effect = download_side_effect

    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
        )
    )

    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["success"] == 1
    assert result_dict["summary"]["failed"] == 1


def test_download_main_files_respects_cancellation(mock_path, mock_base_worker, mock_services: MockServices, tmp_path):
    """Test cancellation after first template."""
    templates = [
        TemplateRecord(id=1, title="T1", main_file="file1.svg"),
        TemplateRecord(id=2, title="T2", main_file="file2.svg"),
    ]
    mock_services.list.return_value = templates
    mock_services.download_file_from_commons.return_value = {"success": True}

    cancel_event = threading.Event()

    def download_with_cancel(*args, **kwargs):
        cancel_event.set()
        return {"success": True, "path": "file.svg"}

    mock_services.download_file_from_commons.side_effect = download_with_cancel

    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
            cancel_event=cancel_event,
        )
    )

    result_dict = mock_base_worker["save_job_result_by_name"].call_args[0][1]
    assert result_dict["summary"]["processed"] == 1
    assert result_dict["status"] == "cancelled"


def test_download_main_files_handles_file_with_file_prefix(mock_path, mock_services: MockServices, tmp_path):
    """Test that 'File:' prefix is handled correctly."""
    templates = [TemplateRecord(id=1, title="T1", main_file="File:Example.svg")]
    mock_services.list.return_value = templates
    mock_services.download_file_from_commons.return_value = {"success": True, "path": "Example.svg"}

    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
        )
    )

    _call = mock_services.download_file_from_commons.call_args[1]
    passed_filename = _call["filename"]
    assert passed_filename == "Example.svg"


def test_download_main_files_checks_if_file_exists(mock_path, mock_services: MockServices, tmp_path):
    """Test worker handles existing files (overwrites by design)."""
    templates = [TemplateRecord(id=1, title="T1", main_file="exists.svg")]
    mock_services.list.return_value = templates
    mock_services.download_file_from_commons.return_value = {"success": True, "path": "exists.svg"}

    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
        )
    )
    assert mock_services.download_file_from_commons.called


def test_download_main_files_fatal_error_handling(mock_path, mock_base_worker, mock_services: MockServices, tmp_path):
    """Test workflow when an error occurs but partial results are saved."""
    mock_services.list.side_effect = Exception("DB Fail")

    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
        )
    )

    mock_base_worker["update_job_status_with_retry"].assert_called_with(
        1, "failed", "download_main_files_job_1.json", job_type="download_main_files"
    )


def test_download_main_files_saves_progress_periodically(
    mock_path, mock_base_worker, mock_services: MockServices, tmp_path
):
    """Test that save_progress is called."""
    templates = [TemplateRecord(id=i, title=f"T{i}", main_file=f"f{i}.svg") for i in range(1, 5)]
    mock_services.list.return_value = templates
    mock_services.download_file_from_commons.return_value = {"success": True}

    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
        )
    )

    assert mock_base_worker["save_job_result_by_name"].call_count >= 2


def test_download_main_files_creates_output_directory(mock_path, mock_services: MockServices, tmp_path):
    """Test that the output directory is created if missing."""
    mock_services.list.return_value = []
    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
        )
    )

    mock_path.return_value.mkdir.assert_called()


def test_download_main_files_generates_zip_on_completion(mock_path, mock_services: MockServices, tmp_path):
    """Test that zip generation is triggered."""
    mock_services.list.return_value = []
    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
        )
    )

    mock_services.generate_main_files_zip.assert_called_once()


def test_download_main_files_no_zip_on_failure(mock_path, mock_services: MockServices, tmp_path):
    """Test that zip generation is skipped if job is failed/cancelled."""
    mock_services.list.side_effect = Exception("Fail")

    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
        )
    )

    mock_services.generate_main_files_zip.assert_not_called()


def test_download_main_files_for_templates_accepts_args_keyword_param(mock_path, mock_services: MockServices):
    """Test entry point unified signature."""
    mock_services.list.return_value = []
    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=1,
            user={},
            args={"some": "val"},
        )
    )


def test_download_main_files_for_templates_args_defaults_to_none(mock_path, mock_services: MockServices):
    """Test entry point works with default args."""
    mock_services.list.return_value = []
    runner.download_main_files_for_templates(
        JobsRunner(
            job_id=99,
            user={},
        )
    )


def test_entry_point_maps_limit_items(mock_services: MockServices):
    """Test that limit_items is mapped."""
    mock_services.list.return_value = []
    with patch(
        "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner.DownloadMainFilesWorker"
    ) as MockWorker:
        mock_instance = MagicMock()
        MockWorker.return_value = mock_instance

        runner.download_main_files_for_templates(
            JobsRunner(
                job_id=1,
                user={},
                args={"limit_items": 123},
            )
        )

        call_args = MockWorker.call_args
        passed_args = call_args[0][3] if len(call_args[0]) > 3 else call_args.kwargs.get("args")
        assert isinstance(passed_args, dict)
        assert passed_args.get("limit_items") == 123


class TestCreateMainFilesZip:
    def test_directory_not_exists(self, monkeypatch):
        mock_settings = MagicMock()
        mock_settings.paths.main_files_path = "/nonexistent/path"
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner.settings",
            mock_settings,
        )

        result, status = create_main_files_zip()
        assert status == 404
        assert "does not exist" in result

    def test_zip_not_found(self, monkeypatch, tmp_path):
        mock_settings = MagicMock()
        mock_settings.paths.main_files_path = str(tmp_path)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner.settings",
            mock_settings,
        )

        result, status = create_main_files_zip()
        assert status == 404
        assert "Zip file not found" in result

    def test_zip_empty(self, monkeypatch, tmp_path):
        zip_path = tmp_path / MAIN_FILES_ZIP_NAME
        zip_path.write_text("")

        mock_settings = MagicMock()
        mock_settings.paths.main_files_path = str(tmp_path)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner.settings",
            mock_settings,
        )

        result, status = create_main_files_zip()
        assert status == 500
        assert "empty or corrupted" in result

    @patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner.send_file")
    def test_zip_found_returns_file(self, mock_send_file, monkeypatch, tmp_path):
        zip_path = tmp_path / MAIN_FILES_ZIP_NAME
        zip_path.write_bytes(b"PK\x03\x04fake zip content")

        mock_settings = MagicMock()
        mock_settings.paths.main_files_path = str(tmp_path)
        monkeypatch.setattr(
            "src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner.settings",
            mock_settings,
        )

        mock_send_file.return_value = MagicMock()
        result, status = create_main_files_zip()
        assert status == 200
        mock_send_file.assert_called_once()


class TestDownloadMainFilesForTemplates:
    @patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner.DownloadMainFilesWorker")
    def test_creates_worker_and_runs(self, mock_worker_cls):
        mock_worker = MagicMock()
        mock_worker_cls.return_value = mock_worker

        cancel_event = MagicMock()
        download_main_files_for_templates(
            JobsRunner(
                job_id=42,
                user={"name": "test"},
                cancel_event=cancel_event,
                args={"key": "value"},
            )
        )

        mock_worker_cls.assert_called_once_with(42, {"name": "test"}, cancel_event, {"key": "value"})
        mock_worker.run.assert_called_once()

    @patch("src.main_app.jobs_workers.admin_jobs_workers.download_main_files.runner.DownloadMainFilesWorker")
    def test_default_args(self, mock_worker_cls):
        mock_worker = MagicMock()
        mock_worker_cls.return_value = mock_worker

        download_main_files_for_templates(
            JobsRunner(
                job_id=1,
                user={},
            )
        )

        mock_worker_cls.assert_called_once_with(1, {}, None, None)
        mock_worker.run.assert_called_once()
