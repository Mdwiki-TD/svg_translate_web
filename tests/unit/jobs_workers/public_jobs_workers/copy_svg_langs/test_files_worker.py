"""
Unit tests for files_worker module.

classes to test: OneFileProcessor
"""

from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from src.main_app.api_services.files_service import DownloadAndSaveData
from src.main_app.api_services.files_service.objects import FileLanguagesMap, UploadResult
from src.main_app.jobs_workers.objects import JobsRunner
from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.objects import FilesProcessedItem
from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker import (
    CopySvgLangsWorker,
)
from src.main_app.services.copysvg_wrapper import InjectResult
from src.main_app.services.copysvg_wrapper.mapping import RepairResult


@dataclass
class MockServices:
    download_and_save: MagicMock
    detect: MagicMock
    fix: MagicMock
    inject: MagicMock
    upload_svg: MagicMock
    get_file_languages: MagicMock
    mw_page: MagicMock
    mw_client_page: MagicMock


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
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.files_worker.NestedStructureService.analyze_file",
        mock_detect,
    )

    mock_fix = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.files_worker.NestedStructureService.repair_file",
        mock_fix,
    )

    mock_inject = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.files_worker.SvgInjector.inject_one_file",
        mock_inject,
    )

    mock_get_langs = MagicMock()
    mock_get_langs.return_value = FileLanguagesMap(langs=["en", "de", "fr"])
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.files_worker.FilesService.get_file_languages",
        mock_get_langs,
    )

    mw_page = MagicMock()
    mw_page.get_text.return_value = "{{Information\n|other versions={{Svg lang|en}}\n}}"
    mw_page.edit.return_value = {"success": True, "newrevid": 999}

    mock_mw_client_page = MagicMock(return_value=mw_page)
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.files_worker.MwClientPage",
        mock_mw_client_page,
    )

    return MockServices(
        download_and_save=mock_download,
        detect=mock_detect,
        fix=mock_fix,
        inject=mock_inject,
        upload_svg=mock_upload,
        get_file_languages=mock_get_langs,
        mw_page=mw_page,
        mw_client_page=mock_mw_client_page,
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
    _worker.save_progress = MagicMock()
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
        assert title_info.status == "failed"
        assert title_info.error == "Failed"

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
        # the original file was still uploaded, so the inject error must not fail the file
        assert title_info.status == "success"
        assert title_info.error is None

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


class TestUpdateLangsStep:
    """Tests for the `update_langs` step that runs after a successful upload."""

    @staticmethod
    def _prepare_upload_success(mock_files_services: MockServices, tmp_path) -> None:
        dl_path = tmp_path / "test.svg"
        dl_path.write_text("<svg></svg>")
        mock_files_services.download_and_save.return_value = DownloadAndSaveData(result="success", path=str(dl_path))
        mock_files_services.detect.return_value = []
        mock_files_services.inject.return_value = InjectResult(
            result=True, msg="ok", new_languages_count=1, updated_translations=0
        )
        mock_files_services.upload_svg.return_value = UploadResult(ok=True, error="", msg="uploaded")

    def test_update_langs_after_upload(
        self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path
    ):
        self._prepare_upload_success(mock_files_services, tmp_path)
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.status == "success"
        assert title_info.steps.update_langs.result is True

        summary = mock_files_services.mw_page.edit.call_args.kwargs["summary"]
        assert summary == "Insert Svg lang (de,fr)"

        new_text = mock_files_services.mw_page.edit.call_args.args[0]
        assert "{{Svg lang|de|fr}}" in new_text
        assert title_info.steps.update_langs.details["newrevid"] == 999

    def test_update_langs_skipped_when_upload_skipped(
        self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path
    ):
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
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "File:Main.svg")

        assert result is False
        assert title_info.steps.upload.msg == "skipped"
        assert title_info.steps.update_langs.result is None
        mock_files_services.mw_page.edit.assert_not_called()

    def test_update_langs_no_text(self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path):
        self._prepare_upload_success(mock_files_services, tmp_path)
        mock_files_services.mw_page.get_text.return_value = ""
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.status == "success"
        assert title_info.steps.upload.result is True
        assert title_info.steps.update_langs.result is False
        assert title_info.error is None

    def test_update_langs_no_langs(self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path):
        self._prepare_upload_success(mock_files_services, tmp_path)
        mock_files_services.get_file_languages.return_value = FileLanguagesMap(langs=["en"])
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.status == "success"
        assert title_info.steps.update_langs.result is None
        assert title_info.steps.update_langs.msg == "Skipped - no languages found"
        mock_files_services.mw_page.edit.assert_not_called()

    def test_update_langs_identical(
        self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path
    ):
        self._prepare_upload_success(mock_files_services, tmp_path)
        mock_files_services.mw_page.get_text.return_value = "{{Information\n|other versions={{Svg lang|de|fr}}\n}}"
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.steps.update_langs.result is None
        assert title_info.steps.update_langs.msg == "Skipped - page content is already identical"
        mock_files_services.mw_page.edit.assert_not_called()

    def test_update_langs_edit_failed(
        self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path
    ):
        self._prepare_upload_success(mock_files_services, tmp_path)
        mock_files_services.mw_page.edit.return_value = {"success": False, "error": "ratelimited"}
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "File:Main.svg")

        # a failed update_langs step does not fail the file itself
        assert result is True
        assert title_info.status == "success"
        assert title_info.error is None
        assert title_info.steps.update_langs.result is False
        assert title_info.steps.update_langs.details["error"] == "ratelimited"

    def test_update_langs_exception_does_not_fail_file(
        self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path
    ):
        self._prepare_upload_success(mock_files_services, tmp_path)
        mock_files_services.get_file_languages.side_effect = ValueError("API error")
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.status == "success"
        assert title_info.error is None
        assert title_info.steps.update_langs.result is False
        assert title_info.steps.update_langs.msg == "Error updating langs"
        assert "API error" in title_info.steps.update_langs.details["error"]

    def test_update_langs_load_langs_error(
        self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path
    ):
        self._prepare_upload_success(mock_files_services, tmp_path)
        mock_files_services.get_file_languages.return_value = FileLanguagesMap(
            langs=None, error="Metadata not found for File:Test.svg"
        )
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker._process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.status == "success"
        assert title_info.error is None
        assert title_info.steps.update_langs.result is False
        assert title_info.steps.update_langs.msg == "Could not load file languages"
        assert title_info.steps.update_langs.details["error"] == "Metadata not found for File:Test.svg"
        mock_files_services.mw_page.edit.assert_not_called()

    def test_update_langs_prefixes_file_title(
        self, mock_worker: CopySvgLangsWorker, mock_files_services: MockServices, tmp_path
    ):
        # titles in this job are stored without the `File:` namespace prefix
        self._prepare_upload_success(mock_files_services, tmp_path)
        title_info = FilesProcessedItem(title="Total daily covid deaths, Africa, Apr 13, 2024.svg")

        result = mock_worker._process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.steps.update_langs.result is True

        used_title = mock_files_services.mw_client_page.call_args.args[0]
        assert used_title == "File:Total daily covid deaths, Africa, Apr 13, 2024.svg"
        assert mock_files_services.get_file_languages.call_args.args[0] == used_title
