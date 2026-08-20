"""
Unit tests for files_worker module.

classes to test: OneFileProcessor
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from src.main_app.api_services.files_service import DownloadAndSaveData
from src.main_app.api_services.files_service.objects import UploadResult
from src.main_app.jobs_workers.objects import JobsRunner
from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.objects import FilesProcessedItem
from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker import (
    CopySvgLangsWorker,
)
from src.main_app.services.copysvg_wrapper import InjectResult
from src.main_app.services.fix_nested.objects import RepairResult


@dataclass
class MockServices:
    download_and_save: MagicMock
    detect: MagicMock
    fix: MagicMock
    inject: MagicMock
    upload_svg: MagicMock


@pytest.fixture
def mock_files_services(monkeypatch: pytest.MonkeyPatch) -> MockServices:

    mock_download = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.FilesService.download_and_save",
        mock_download,
    )

    mock_upload = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.files_worker.UploadService.upload_svg",
        mock_upload,
    )

    mock_detect = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.files_worker.MatchFixNestedTags.analyze_file",
        mock_detect,
    )

    mock_fix = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.files_worker.MatchFixNestedTags.repair_file",
        mock_fix,
    )

    mock_inject = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.files_worker.inject_step_one_file", mock_inject
    )

    return MockServices(
        download_and_save=mock_download,
        detect=mock_detect,
        fix=mock_fix,
        inject=mock_inject,
        upload_svg=mock_upload,
    )


@pytest.fixture
def mock_worker():
    user = {"username": "testuser", "id": 123}
    args = {"title": "File:Test.svg", "upload": True}
    _worker = CopySvgLangsWorker(
        JobsRunner(
            job_id=1,
            user=user,
            args=args,
        )
    )
    _worker._save_progress = MagicMock()
    return _worker


class TestCopySvgLangsWorkerProcessOne:
    def test_download_exception(self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices):
        mock_files_services.download_and_save.side_effect = ValueError("Network error")
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "")

        assert result is False
        assert title_info.steps.download.result is False
        assert title_info.steps.download.msg == "Error downloading"
        assert title_info.status == "failed"

    def test_download_not_ok(self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices):
        mock_files_services.download_and_save.return_value = DownloadAndSaveData(result="failed", path=None)
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "")

        assert result is False
        assert title_info.steps.download.result is False
        assert title_info.status == "failed"

    def test_download_no_file_path(self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices):
        mock_files_services.download_and_save.return_value = DownloadAndSaveData(result="error", path=None)
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "")

        assert result is False
        assert title_info.steps.download.result is False
        assert title_info.status == "failed"

    def test_no_nested_tags(self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_files_services.download_and_save.return_value = DownloadAndSaveData(result="success", path=str(dl_path))
        mock_files_services.detect.return_value = []
        mock_files_services.inject.return_value = InjectResult(result=None, msg="No changes")

        title_info = FilesProcessedItem(title="File:Test.svg")

        _result = mock_worker._process_one_item(title_info, "")

        assert title_info.steps.nested.result is None
        assert title_info.steps.nested.msg == "No nested tags found"

    def test_fix_nested_tags_fails(self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_files_services.download_and_save.return_value = DownloadAndSaveData(result="success", path=str(dl_path))
        mock_files_services.detect.return_value = [1, 2]
        mock_files_services.fix.return_value = RepairResult(success=False, len_tags_before_fix=2, len_tags_after_fix=2)
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "")

        assert result is False
        assert title_info.steps.nested.result is False
        assert title_info.status == "failed"
        assert title_info.steps.inject.msg == "skipped"
        assert title_info.steps.upload.msg == "skipped"

    def test_verify_fix_zero(self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_files_services.download_and_save.return_value = DownloadAndSaveData(result="success", path=str(dl_path))
        mock_files_services.detect.return_value = [1, 2]
        mock_files_services.fix.return_value = RepairResult(success=True, len_tags_before_fix=2, len_tags_after_fix=2)
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "")

        assert result is False
        assert title_info.steps.nested.result is False
        assert title_info.status == "failed"

    def test_inject_success_uploads(self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_files_services.download_and_save.return_value = DownloadAndSaveData(result="success", path=str(dl_path))
        mock_files_services.detect.return_value = []
        mock_files_services.inject.return_value = InjectResult(
            result=True, msg="ok", new_languages_count=1, updated_translations=0
        )
        mock_files_services.upload_svg.return_value = UploadResult(ok=True, error="", msg="uploaded")
        mock_worker.main_title = "Main.svg"
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "")

        assert result is True
        assert title_info.steps.upload.result is True
        assert title_info.status == "success"

    def test_inject_none_no_nested_tags(
        self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path
    ):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_files_services.download_and_save.return_value = DownloadAndSaveData(result="success", path=str(dl_path))
        mock_files_services.detect.return_value = []
        mock_files_services.inject.return_value = InjectResult(result=None, msg="No changes")
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "")

        assert result is False

    def test_inject_false_no_nested_tags(
        self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path
    ):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_files_services.download_and_save.return_value = DownloadAndSaveData(result="success", path=str(dl_path))
        mock_files_services.detect.return_value = []
        mock_files_services.inject.return_value = InjectResult(result=False, msg="Failed")
        title_info = FilesProcessedItem(title="File:Test.svg", steps=MagicMock(inject=MagicMock(result=False)))

        result = mock_worker._process_one_item(title_info, "")

        assert result is False

    def test_inject_false_but_nested_fixed(
        self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path
    ):
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_files_services.download_and_save.return_value = DownloadAndSaveData(result="success", path=str(dl_path))
        mock_files_services.detect.return_value = [1, 2]
        mock_files_services.fix.return_value = RepairResult(success=True, len_tags_before_fix=2, len_tags_after_fix=0)
        mock_files_services.inject.return_value = InjectResult(result=False, msg="Failed")
        mock_files_services.upload_svg.return_value = UploadResult(ok=True, msg="uploaded", error="")

        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "")

        # nested step not updated on success (stays default)
        assert title_info.steps.nested.result is True
        assert title_info.steps.nested.msg == "Fixed 2 nested tag(s)"
        assert title_info.steps.inject.result is False
        assert title_info.steps.inject.msg == "Failed"
        assert result is True

    def test_upload_disabled(self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path):
        mock_worker.config = mock_worker._load_config({"upload": False})
        mock_worker.config.output_dir = tmp_path
        mock_worker.files_processor.config = mock_worker.config

        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_files_services.download_and_save.return_value = DownloadAndSaveData(result="success", path=str(dl_path))
        mock_files_services.detect.return_value = []
        mock_files_services.inject.return_value = InjectResult(
            result=True, msg="ok", new_languages_count=1, updated_translations=0
        )
        mock_worker.main_title = "Main.svg"
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "")

        assert result is False
        assert title_info.steps.upload.result is None
        assert title_info.steps.upload.msg == "skipped"

        assert title_info.steps.upload.details is not None
        assert "Upload disabled" in title_info.steps.upload.details["error"]

        assert title_info.status == "skipped"
