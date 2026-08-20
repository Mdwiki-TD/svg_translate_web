"""Unit tests for copy_svg_langs worker module."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.main_app.api_services.files_service import DownloadAndSaveData
from src.main_app.api_services.files_service.objects import UploadResult
from src.main_app.jobs_workers.objects import JobsRunner
from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.objects import FilesProcessedItem
from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker import (
    CopySvgLangsWorker,
)
from src.main_app.services.copysvg_wrapper import ExtractResult, InjectResult


@dataclass
class MockSteps:
    text: MagicMock
    titles: MagicMock
    translations: MagicMock


@dataclass
class MockServices:
    check_cancel_db_periodic: MagicMock
    is_cancelled: MagicMock
    download_and_save: MagicMock
    detect: MagicMock
    inject: MagicMock
    upload_svg: MagicMock


@pytest.fixture
def mock_steps(monkeypatch: pytest.MonkeyPatch) -> MockSteps:

    mock_text = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_text_step", mock_text
    )

    mock_titles = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_titles_step", mock_titles
    )

    mock_translations = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.extract_from_path", mock_translations
    )

    return MockSteps(
        text=mock_text,
        titles=mock_titles,
        translations=mock_translations,
    )


@pytest.fixture
def mock_copylangs_services(monkeypatch: pytest.MonkeyPatch) -> MockServices:

    mock_check_cancel_db_periodic = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.CopySvgLangsWorker.check_cancel_db_periodic",
        mock_check_cancel_db_periodic,
    )

    mock_is_cancelled = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.worker.CopySvgLangsWorker.is_cancelled",
        mock_is_cancelled,
    )

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

    mock_inject = MagicMock()
    monkeypatch.setattr(
        "src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.files_worker.inject_step_one_file", mock_inject
    )

    return MockServices(
        check_cancel_db_periodic=mock_check_cancel_db_periodic,
        is_cancelled=mock_is_cancelled,
        download_and_save=mock_download,
        detect=mock_detect,
        inject=mock_inject,
        upload_svg=mock_upload,
    )


@pytest.fixture
def mock_clients(monkeypatch: pytest.MonkeyPatch, mock_site):
    """"""
    mock_get_user_site = MagicMock(return_value=mock_site)

    monkeypatch.setattr("src.main_app.jobs_workers.base_worker.JobsService.update_job_status", MagicMock())
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.JobsService.update_job_status_with_retry",
        MagicMock(),
    )
    monkeypatch.setattr("src.main_app.jobs_workers.base_worker.save_job_result_by_name", MagicMock())
    monkeypatch.setattr(
        "src.main_app.jobs_workers.base_worker.get_user_site",
        mock_get_user_site,
    )
    m_session = MagicMock()
    m_session.return_value = MagicMock()
    monkeypatch.setattr(
        "src.main_app.api_services.files_service.service.create_commons_session",
        m_session,
    )
    return {
        "session": m_session,
        "site": mock_get_user_site,
    }


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


class TestCopySvgLangsWorker:
    def test_get_job_type(self) -> None:
        worker = CopySvgLangsWorker(
            JobsRunner(
                job_id=1,
                user={},
                args={"title": "Test.svg"},
            )
        )
        assert worker.get_job_type() == "copy_svg_langs"

    def test_initial_result_structure(self) -> None:
        worker = CopySvgLangsWorker(
            JobsRunner(
                job_id=1,
                user={},
                args={"title": "Test.svg"},
            )
        )
        result = worker.result

        assert result.status == "pending"
        assert result.started_at is not None
        assert result.completed_at is None
        assert result.cancelled_at is None
        assert result.title is None
        assert result.stages.text.status == "pending"
        assert result.stages.titles.status == "pending"
        assert result.stages.translations.status == "pending"

    def test_worker_init_with_user(self) -> None:
        user = {"username": "testuser", "id": 123}
        worker = CopySvgLangsWorker(
            JobsRunner(
                job_id=1,
                args={"title": "Test.svg"},
                user=user,
            )
        )
        assert worker.user == user

    def test_worker_init_with_cancel_event(self) -> None:
        cancel_event = threading.Event()
        worker = CopySvgLangsWorker(
            JobsRunner(
                job_id=1,
                user={},
                args={"title": "Test.svg"},
                cancel_event=cancel_event,
            )
        )
        assert worker.cancel_event is cancel_event

    def test_worker_reads_upload_limit_from_args(self) -> None:
        worker = CopySvgLangsWorker(
            JobsRunner(
                job_id=1,
                user={},
                args={"title": "Test.svg", "upload_limit": 5},
            )
        )
        assert worker.files_processor.config.upload_limit == 5

    def test_worker_defaults_upload_limit_when_args_none(self) -> None:
        worker = CopySvgLangsWorker(
            JobsRunner(
                job_id=1,
                user={},
                args=None,
            )
        )
        assert worker.files_processor.config.upload_limit == 0

    def test_worker_upload_limit_none_when_key_missing(self) -> None:
        worker = CopySvgLangsWorker(
            JobsRunner(
                job_id=1,
                user={},
                args={"title": "Test.svg"},
            )
        )
        assert worker.files_processor.config.upload_limit == 0


class TestCopySvgLangsWorkerProcess:
    def test_process_no_title(self, mock_worker: CopySvgLangsWorker, mock_clients):
        mock_worker.title = None
        result = mock_worker.process()
        assert result.status == "failed"

    def test_process_success(
        self,
        mock_copylangs_services: MockServices,
        mock_worker: CopySvgLangsWorker,
        mock_steps: MockSteps,
        mock_clients,
        tmp_path,
    ):
        # mock_worker.config = mock_worker._load_config()
        mock_worker.config.output_dir = tmp_path

        mock_steps.text.return_value = {"success": True, "text": "some text"}
        mock_steps.titles.return_value = {"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]}
        mock_steps.translations.return_value = ExtractResult.from_any(
            {"success": True, "translations": {"new": {"key": {"en": "Text"}}}}
        )
        mock_copylangs_services.download_and_save.return_value = DownloadAndSaveData(result="success", path="path.svg")
        mock_copylangs_services.detect.return_value = []
        mock_copylangs_services.inject.return_value = InjectResult(
            result=True, msg="ok", new_languages_count=1, updated_translations=0
        )
        mock_copylangs_services.upload_svg.return_value = UploadResult(ok=True, error="", msg="uploaded")

        mock_copylangs_services.is_cancelled.return_value = False

        result = mock_worker.process()

        # BaseObjectsJobWorker.run sets it to completed, but process() returns current state
        assert result.error is None
        assert result.failed_at is None
        assert result.stages.translations.message != "Error when downloading main file: Main.svg"
        assert result.stages.translations.status == "completed"

        assert result.status == "pending"

    def test_process_stage_fails(self, mock_worker: CopySvgLangsWorker, mock_steps: MockSteps, mock_clients):
        mock_steps.text.return_value = {"success": False, "error": "Extraction failed"}

        result = mock_worker.process()

        assert result.status == "failed"
        assert result.stages.text.status == "failed"
        assert result.stages.text.message == "Extraction failed"

    def test_process_auth_failed(self, mock_worker: CopySvgLangsWorker, mock_clients, tmp_path):
        mock_worker.config.output_dir = tmp_path
        mock_worker.files_processor.config.output_dir = tmp_path

        mock_clients["site"].return_value = None

        result = mock_worker.process()

        assert result.errors[0].get("error") == "No authenticated user site available."

    def test_process_cancelled(
        self, mock_worker: CopySvgLangsWorker, mock_clients, mock_copylangs_services: MockServices
    ):
        mock_copylangs_services.is_cancelled.return_value = True
        result = mock_worker.process()
        assert result.stages.text.status == "cancelled"

    def test_compute_output_dir_none(self, mock_worker: CopySvgLangsWorker):
        assert mock_worker._compute_output_dir(None) is None


class TestCopySvgLangsWorkerInjectStepFile:
    """tests for the inject_step_file function"""

    def test_no_file_path(self, mock_worker: CopySvgLangsWorker):
        title_info = FilesProcessedItem(title="File:Test.svg")
        new_path = mock_worker.files_processor.inject_step_file(title_info, "")
        step_result = title_info.steps.inject

        assert step_result.result is False
        assert step_result.msg == "No file path found"
        assert new_path is None

    def test_inject_result_none(self, mock_worker: CopySvgLangsWorker, mock_copylangs_services: MockServices, tmp_path):
        mock_worker.config.output_dir = tmp_path
        mock_copylangs_services.inject.return_value = MagicMock(result=None, msg="No changes")

        title_info = FilesProcessedItem(title="File:Test.svg")

        new_path = mock_worker.files_processor.inject_step_file(title_info, tmp_path / "test.svg")
        step_result = title_info.steps.inject

        assert step_result.result is None
        assert step_result.msg == "No changes"
        assert new_path is None

    def test_inject_result_false(
        self, mock_worker: CopySvgLangsWorker, mock_copylangs_services: MockServices, tmp_path
    ):
        mock_worker.config.output_dir = tmp_path

        mock_copylangs_services.inject.return_value = MagicMock(result=False, msg="Nested tspan error")

        title_info = FilesProcessedItem(title="File:Test.svg")
        new_path = mock_worker.files_processor.inject_step_file(title_info, tmp_path / "test.svg")
        step_result = title_info.steps.inject

        assert step_result.result is False
        assert step_result.msg == "Nested tspan error"
        assert new_path is None

    def test_inject_result_true(self, mock_worker: CopySvgLangsWorker, mock_copylangs_services: MockServices, tmp_path):
        mock_worker.config.output_dir = tmp_path
        mock_worker.files_processor.config.output_dir = tmp_path

        mock_copylangs_services.inject.return_value = InjectResult(
            result=True,
            msg="2 languages injected",
            new_languages_count=2,
            languages_after=["ar", "de"],
            updated_translations=1,
        )

        file_name = "test.svg"
        file_path = tmp_path / file_name
        file_path.write_text("")
        title_info = FilesProcessedItem(title="File:Test.svg")
        new_path = mock_worker.files_processor.inject_step_file(title_info, file_path)
        step_result = title_info.steps.inject

        assert step_result.result is True
        assert step_result.msg == "2 languages injected"
        assert title_info.steps.translations.details == {
            "new": 2,
            "updated": 1,
            "new_list": ["ar", "de"],
            "inserted": 0,
        }
        assert new_path == tmp_path / "translated" / file_name


class TestCopySvgLangsWorkerUploadStep:
    def test_upload_disabled(self, mock_worker: CopySvgLangsWorker):
        mock_worker.config = mock_worker._load_config({"upload": False})
        mock_worker.files_processor.config = mock_worker.config

        title_info = FilesProcessedItem("")

        result = mock_worker.files_processor._upload_step(title_info, "summary", Path("test.svg"))

        assert result is False
        assert title_info.steps.upload.result is None
        assert title_info.steps.upload.msg == "skipped"
        assert title_info.status == "skipped"

    def test_upload_limit_reached(self, mock_worker: CopySvgLangsWorker):
        mock_worker.config = mock_worker._load_config({"upload": True})
        mock_worker.files_processor.config = mock_worker.config

        mock_worker.files_processor.config.upload_limit = 5
        mock_worker.files_processor.upload_done = 5
        title_info = FilesProcessedItem("")

        result = mock_worker.files_processor._upload_step(title_info, "summary", Path("test.svg"))

        assert result is False
        assert title_info.steps.upload.msg == "skipped"

        assert title_info.steps.upload.details is not None
        assert "Upload limit reached" in title_info.steps.upload.details["error"]

        assert title_info.status == "skipped"

    def test_upload_success(self, mock_worker: CopySvgLangsWorker, mock_copylangs_services: MockServices):
        mock_worker.config = mock_worker._load_config({"upload": True})
        mock_worker.files_processor.config = mock_worker.config

        mock_worker.files_processor.config.upload_limit = 5
        mock_worker.files_processor.upload_done = 0
        mock_worker.site = MagicMock()

        mock_copylangs_services.upload_svg.return_value = UploadResult(ok=True, error="", msg="uploaded")
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker.files_processor._upload_step(title_info, "Adding translations", Path("test.svg"))

        assert result is True
        assert title_info.steps.upload.result is True
        assert title_info.steps.upload.msg == "File Successfully uploaded."
        assert title_info.status == "success"
        assert mock_worker.files_processor.upload_done == 1

    def test_upload_skipped(self, mock_worker: CopySvgLangsWorker, mock_copylangs_services: MockServices):
        mock_worker.config = mock_worker._load_config({"upload": True})
        mock_worker.files_processor.config = mock_worker.config

        mock_worker.site = MagicMock()

        mock_copylangs_services.upload_svg.return_value = UploadResult(
            ok=None, error="skipped", msg="File exists", error_details=""
        )
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker.files_processor._upload_step(title_info, "Adding translations", Path("test.svg"))

        assert result is False
        assert title_info.steps.upload.result is None
        assert title_info.steps.upload.msg == "File exists"

    def test_upload_failure(self, mock_worker: CopySvgLangsWorker, mock_copylangs_services: MockServices):
        mock_worker.config = mock_worker._load_config({"upload": True})
        mock_worker.files_processor.config = mock_worker.config

        mock_worker.site = MagicMock()

        mock_copylangs_services.upload_svg.return_value = UploadResult(
            ok=False, error="Upload failed", msg="error", error_details="details"
        )
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = mock_worker.files_processor._upload_step(title_info, "Adding translations", Path("test.svg"))

        assert result is False
        assert title_info.steps.upload.result is False
        assert title_info.steps.upload.msg == "Upload failed."
        assert title_info.error == "Upload failed"


class TestCopySvgLangsWorkerLimits:
    def test_apply_limits_applied(self, mock_worker: CopySvgLangsWorker):
        mock_worker.config.limit_items = 2
        titles = ["a.svg", "b.svg", "c.svg", "d.svg"]

        result = mock_worker._apply_limits(titles)

        assert len(result) == 2
        assert result == ["a.svg", "b.svg"]

    def test_apply_limits_no_limit(self, mock_worker: CopySvgLangsWorker):
        mock_worker.config.limit_items = 0
        titles = ["a.svg", "b.svg", "c.svg"]

        result = mock_worker._apply_limits(titles)

        assert len(result) == 3

    def test_apply_limits_below_limit(self, mock_worker: CopySvgLangsWorker):
        mock_worker.config.limit_items = 5
        titles = ["a.svg"]

        result = mock_worker._apply_limits(titles)

        assert len(result) == 1


class TestCopySvgLangsWorkerProcessAdvanced:
    def test_process_titles_fails(self, mock_worker: CopySvgLangsWorker, mock_steps: MockSteps, mock_clients):
        mock_steps.text.return_value = {"success": True, "text": "some text"}
        mock_steps.titles.return_value = {"success": False, "error": "Title extraction failed"}

        result = mock_worker.process()

        assert result.status == "failed"
        assert result.stages.titles.status == "failed"
        assert result.stages.titles.message == "Title extraction failed"

    def test_process_translations_fails(self, mock_worker: CopySvgLangsWorker, mock_steps: MockSteps, mock_clients):
        mock_steps.text.return_value = {"success": True, "text": "some text"}
        mock_steps.titles.return_value = {"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]}
        mock_steps.translations.return_value = ExtractResult.from_any(
            {"success": False, "error": "Translation extraction failed"}
        )

        result = mock_worker.process()

        assert result.status == "failed"
        assert result.stages.translations.status == "failed"

    def test_process_cancelled_during_loop(
        self,
        mock_copylangs_services: MockServices,
        mock_worker: CopySvgLangsWorker,
        mock_steps: MockSteps,
        mock_clients,
        tmp_path,
    ):
        mock_worker.config.output_dir = tmp_path
        mock_worker.files_processor.config.output_dir = tmp_path

        mock_steps.text.return_value = {"success": True, "text": "some text"}
        mock_steps.titles.return_value = {"success": True, "main_title": "Main.svg", "titles": ["File1.svg"]}
        mock_steps.translations.return_value = ExtractResult.from_any(
            {"success": True, "translations": {"new": {"key": {"en": "Text"}}}}
        )
        mock_copylangs_services.download_and_save.return_value = DownloadAndSaveData(
            result="success", path=str(tmp_path / "test.svg")
        )

        mock_copylangs_services.is_cancelled.side_effect = [False, False, True]

        mock_copylangs_services.detect.return_value = []
        result = mock_worker.process()

        assert result.stages.processfiles.status == "cancelled"

    def test_process_periodic_cancel(
        self,
        mock_copylangs_services: MockServices,
        mock_worker: CopySvgLangsWorker,
        mock_steps: MockSteps,
        mock_clients,
        tmp_path,
    ):
        mock_worker.config.output_dir = tmp_path
        mock_worker.files_processor.config.output_dir = tmp_path

        mock_steps.text.return_value = {"success": True, "text": "some text"}
        mock_steps.titles.return_value = {
            "success": True,
            "main_title": "Main.svg",
            "titles": ["File1.svg", "File2.svg"],
        }
        mock_steps.translations.return_value = ExtractResult.from_any(
            {"success": True, "translations": {"new": {"key": {"en": "Text"}}}}
        )
        mock_copylangs_services.download_and_save.return_value = DownloadAndSaveData(result="success", path="path.svg")
        mock_copylangs_services.detect.return_value = []

        mock_copylangs_services.is_cancelled.return_value = False

        mock_copylangs_services.inject.return_value = InjectResult(
            result=True, msg="ok", new_languages_count=0, updated_translations=0
        )
        mock_copylangs_services.check_cancel_db_periodic.return_value = True
        mock_copylangs_services.upload_svg.return_value = UploadResult(ok=True, error="", msg="uploaded")

        result = mock_worker.process()

        # periodic check breaks loop early - only first file processed
        assert len(result.files_success) == 1
        assert len(result.files_processed) == 0

    def test_process_multiple_files_progress_save(
        self,
        mock_worker: CopySvgLangsWorker,
        mock_copylangs_services: MockServices,
        mock_steps: MockSteps,
        mock_clients,
        tmp_path,
    ):
        mock_worker.config.output_dir = tmp_path
        mock_worker.files_processor.config.output_dir = tmp_path

        mock_steps.text.return_value = {"success": True, "text": "some text"}
        mock_steps.titles.return_value = {
            "success": True,
            "main_title": "Main.svg",
            "titles": ["F1.svg", "F2.svg", "F3.svg"],
        }
        mock_steps.translations.return_value = ExtractResult.from_any(
            {"success": True, "translations": {"new": {"key": {"en": "Text"}}}}
        )
        mock_copylangs_services.download_and_save.return_value = DownloadAndSaveData(result="success", path="path.svg")
        mock_copylangs_services.detect.return_value = []
        mock_copylangs_services.is_cancelled.return_value = False
        mock_copylangs_services.inject.return_value = InjectResult(result=None, msg="No changes")
        mock_copylangs_services.check_cancel_db_periodic.return_value = False

        result = mock_worker.process()

        assert result.stages.processfiles.status == "completed"

    def test_title_info_status_normalized(
        self,
        mock_copylangs_services: MockServices,
        mock_worker: CopySvgLangsWorker,
        mock_steps: MockSteps,
        mock_clients,
        tmp_path,
    ):
        mock_worker.config.output_dir = tmp_path
        mock_worker.files_processor.config.output_dir = tmp_path

        mock_steps.text.return_value = {"success": True, "text": "some text"}
        mock_steps.titles.return_value = {"success": True, "main_title": "Main.svg", "titles": ["F1.svg"]}
        mock_steps.translations.return_value = ExtractResult.from_any(
            {"success": True, "translations": {"new": {"key": {"en": "Text"}}}}
        )
        mock_copylangs_services.download_and_save.return_value = DownloadAndSaveData(result="success", path="path.svg")
        mock_copylangs_services.detect.return_value = []
        mock_copylangs_services.is_cancelled.return_value = False
        mock_copylangs_services.inject.return_value = InjectResult(result=None, msg="No changes")
        mock_copylangs_services.check_cancel_db_periodic.return_value = False

        result = mock_worker.process()

        assert len(result.files_skipped) == 1
        assert result.files_skipped[0].status == "skipped"


class TestCopySvgLangsWorkerStageMethods:
    def test_extract_titles_step_cancelled(
        self, mock_worker: CopySvgLangsWorker, mock_copylangs_services: MockServices
    ):
        mock_worker.text = "some text"
        mock_copylangs_services.is_cancelled.return_value = True

        result = mock_worker._extract_titles_step()

        assert result is False
        assert mock_worker.result.stages.titles.status == "cancelled"

    def test_extract_titles_step_exception(self, mock_worker: CopySvgLangsWorker, mock_steps: MockSteps):
        mock_worker.text = "some text"
        mock_steps.titles.side_effect = ValueError("bad data")

        result = mock_worker._extract_titles_step()

        assert result is False
        assert mock_worker.result.stages.titles.status == "failed"
        assert mock_worker.result.status == "failed"

    def test_extract_titles_step_failed(self, mock_worker: CopySvgLangsWorker, mock_steps: MockSteps):
        mock_worker.text = "some text"
        mock_steps.titles.return_value = {"success": False, "error": "No titles found"}

        result = mock_worker._extract_titles_step()

        assert result is False
        assert mock_worker.result.stages.titles.status == "failed"
        assert mock_worker.result.stages.titles.message == "No titles found"

    def test_extract_titles_step_message_from_result(self, mock_worker: CopySvgLangsWorker, mock_steps: MockSteps):
        mock_worker.text = "some text"
        mock_steps.titles.return_value = {"success": False, "error": "error", "message": "No titles"}

        mock_worker._extract_titles_step()

        assert mock_worker.result.stages.titles.message == "error"

    def test_extract_translations_step_exception(
        self, mock_worker: CopySvgLangsWorker, mock_steps: MockSteps, tmp_path
    ):
        mock_worker.main_title = "Main.svg"
        mock_worker.config.output_dir = tmp_path
        mock_worker.files_processor.config.output_dir = tmp_path

        mock_steps.translations.side_effect = RuntimeError("DB error")

        result = mock_worker._extract_translations_step()

        assert result is False
        assert mock_worker.result.stages.translations.status == "failed"
        assert mock_worker.result.status == "failed"

    def test_extract_translations_step_failed(self, mock_worker: CopySvgLangsWorker, mock_steps: MockSteps, tmp_path):
        mock_worker.main_title = "Main.svg"
        mock_worker.config.output_dir = tmp_path
        mock_worker.files_processor.config.output_dir = tmp_path

        mock_steps.translations.return_value = ExtractResult.from_any({"success": False, "error": "No translations"})

        result = mock_worker._extract_translations_step()

        assert result is False
        assert mock_worker.result.stages.translations.status == "failed"

    def test_extract_text_step_exception(self, mock_worker: CopySvgLangsWorker, mock_steps: MockSteps):
        mock_worker.title = "File:Test.svg"
        mock_worker.site = MagicMock()

        mock_steps.text.side_effect = ValueError("connection error")

        result = mock_worker._extract_text_step()

        assert result is False
        assert mock_worker.result.stages.text.status == "failed"
        assert mock_worker.result.status == "failed"


class TestCopySvgLangsWorkerComputeOutputDir:
    def test_compute_output_dir_none(self, mock_worker: CopySvgLangsWorker):
        assert mock_worker._compute_output_dir(None) is None

    def test_compute_output_dir_creates_dirs(self, mock_worker: CopySvgLangsWorker, tmp_path):
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_worker._compute_output_dir("File:Test File.svg")

            assert mock_mkdir.call_count == 3
