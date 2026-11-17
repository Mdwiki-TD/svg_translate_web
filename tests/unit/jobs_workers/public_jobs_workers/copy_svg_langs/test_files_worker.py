"""
Unit tests for files_worker module.

classes to test: OneFileProcessor
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from src.main_app.api_services.files_service import DownloadAndSaveData, FileLanguagesMap, UploadResult
from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs import (
    FilesProcessedItem,
    OneFileProcessor,
    SvgLangsConfig,
)
from src.main_app.services.copysvg_wrapper import InjectResult, RepairResult


@pytest.fixture
def mock_deps(tmp_path) -> MagicMock:
    """Consolidated fixture to manage all common mock services and avoid fixture bloat."""
    services = MagicMock()

    # Default successful states
    services.files_service.get_file_languages.return_value = FileLanguagesMap(langs=["en", "de", "fr"])
    dl_path = tmp_path / "test.svg"
    dl_path.write_text("<svg></svg>")
    services.files_service.download_and_save.return_value = DownloadAndSaveData(result="success", path=str(dl_path))

    services.upload_service.upload_svg.return_value = UploadResult(ok=True, error="", msg="uploaded")
    services.svg_injector.inject_one_file.return_value = InjectResult(result=None, msg="No changes")

    services.nested_processor.analyze_file.return_value = []
    services.nested_processor.repair_file.return_value = RepairResult(
        success=True, len_tags_before_fix=2, len_tags_after_fix=0
    )

    # MediaWiki page mock setup
    mw_page = MagicMock()
    mw_page.get_text.return_value = "{{Information\n|other versions={{Svg lang|en}}\n}}"
    mw_page.edit.return_value = {"success": True, "newrevid": 999}

    mw_client_page = MagicMock()
    mw_client_page.return_value = mw_page
    mw_client_page.load.return_value = mw_page

    services.mw_client_page = mw_client_page
    services.mw_page = mw_page

    return services


@pytest.fixture
def files_processor(tmp_path, mock_deps) -> OneFileProcessor:
    """Factory-like fixture to initialize OneFileProcessor with consolidated dependencies."""
    args = {"title": "File:Test.svg", "upload": True}
    return OneFileProcessor(
        config=SvgLangsConfig.load(
            title="File:Test.svg",
            args=args,
            svg_data_path=tmp_path / "svg_data",
        ),
        files_service=mock_deps.files_service,
        upload_service=mock_deps.upload_service,
        mw_client_cls=mock_deps.mw_client_page,
        svg_injector=mock_deps.svg_injector,
        nested_processor=mock_deps.nested_processor,
        site=MagicMock(),
    )


class TestCopySvgLangsWorkerProcessOne:
    def test_download_exception(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        mock_deps.files_service.download_and_save.side_effect = ValueError("Network error")
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "")

        assert result is False
        assert title_info.steps.download.result is False
        assert title_info.steps.download.msg == "Error downloading"
        assert title_info.status == "failed"

    def test_download_not_ok(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        mock_deps.files_service.download_and_save.return_value = DownloadAndSaveData(result="failed", path=None)
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "")

        assert result is False
        assert title_info.steps.download.result is False
        assert title_info.status == "failed"

    def test_download_no_file_path(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        mock_deps.files_service.download_and_save.return_value = DownloadAndSaveData(result="error", path=None)
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "")

        assert result is False
        assert title_info.steps.download.result is False
        assert title_info.status == "failed"

    def test_no_nested_tags(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        mock_deps.nested_processor.analyze_file.return_value = []
        mock_deps.svg_injector.inject_one_file.return_value = InjectResult(result=None, msg="No changes")

        title_info = FilesProcessedItem(title="File:Test.svg")

        _result = files_processor.process_one_item(title_info, "")

        assert title_info.steps.nested.result is None
        assert title_info.steps.nested.msg == "No nested tags found"

    def test_fix_nested_tags_fails(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        mock_deps.nested_processor.analyze_file.return_value = [1, 2]
        mock_deps.nested_processor.repair_file.return_value = RepairResult(
            success=False, len_tags_before_fix=2, len_tags_after_fix=2
        )
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "")

        assert result is False
        assert title_info.steps.nested.result is False
        assert title_info.status == "failed"
        assert title_info.steps.inject.msg == "skipped"
        assert title_info.steps.upload.msg == "skipped"

    def test_verify_fix_zero(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        mock_deps.nested_processor.analyze_file.return_value = [1, 2]
        mock_deps.nested_processor.repair_file.return_value = RepairResult(
            success=True, len_tags_before_fix=2, len_tags_after_fix=2
        )
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "")

        assert result is False
        assert title_info.steps.nested.result is False
        assert title_info.status == "failed"

    def test_inject_success_uploads(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        mock_deps.nested_processor.analyze_file.return_value = []
        mock_deps.svg_injector.inject_one_file.return_value = InjectResult(
            result=True, msg="ok", new_languages_count=1, updated_translations=0
        )
        mock_deps.upload_service.upload_svg.return_value = UploadResult(ok=True, error="", msg="uploaded")
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "Main.svg")

        assert result is True
        assert title_info.steps.upload.result is True
        assert title_info.status == "success"

    def test_inject_none_no_nested_tags(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        mock_deps.nested_processor.analyze_file.return_value = []
        mock_deps.svg_injector.inject_one_file.return_value = InjectResult(result=None, msg="No changes")
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "")

        assert result is False

    def test_inject_false_no_nested_tags(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        mock_deps.nested_processor.analyze_file.return_value = []
        mock_deps.svg_injector.inject_one_file.return_value = InjectResult(result=False, msg="Failed")
        title_info = FilesProcessedItem(title="File:Test.svg", steps=MagicMock(inject=MagicMock(result=False)))

        result = files_processor.process_one_item(title_info, "")

        assert result is False
        assert title_info.status == "failed"
        assert title_info.error == "Failed"

    def test_inject_false_but_nested_fixed(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        mock_deps.nested_processor.analyze_file.return_value = [1, 2]
        mock_deps.nested_processor.repair_file.return_value = RepairResult(
            success=True, len_tags_before_fix=2, len_tags_after_fix=0
        )
        mock_deps.svg_injector.inject_one_file.return_value = InjectResult(result=False, msg="Failed")
        mock_deps.upload_service.upload_svg.return_value = UploadResult(ok=True, msg="uploaded", error="")

        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "")

        assert title_info.steps.nested.result is True
        assert title_info.steps.nested.msg == "Fixed 2 nested tag(s)"
        assert title_info.steps.inject.result is False
        assert title_info.steps.inject.msg == "Failed"
        assert result is True
        assert title_info.status == "success"
        assert title_info.error is None

    def test_upload_disabled(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
        tmp_path,
    ):
        files_processor.config.upload = False
        files_processor.config.output_dir = tmp_path

        mock_deps.nested_processor.analyze_file.return_value = []
        mock_deps.svg_injector.inject_one_file.return_value = InjectResult(
            result=True, msg="ok", new_languages_count=1, updated_translations=0
        )
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "Main.svg")

        assert result is False
        assert title_info.steps.upload.result is None
        assert title_info.steps.upload.msg == "skipped"

        assert title_info.steps.upload.details is not None
        assert "Upload disabled" in title_info.steps.upload.details["error"]

        assert title_info.status == "skipped"


class TestUpdateLangsStep:
    """Tests for the `update_langs` step that runs after a successful upload."""

    @staticmethod
    def _prepare_upload_success(
        mock_deps,
    ) -> None:
        mock_deps.nested_processor.analyze_file.return_value = []
        mock_deps.svg_injector.inject_one_file.return_value = InjectResult(
            result=True, msg="ok", new_languages_count=1, updated_translations=0
        )
        mock_deps.upload_service.upload_svg.return_value = UploadResult(ok=True, error="", msg="uploaded")

    def test_update_langs_after_upload(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        self._prepare_upload_success(mock_deps)
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.status == "success"
        assert title_info.steps.update_langs.result is True

        summary = mock_deps.mw_page.edit.call_args.kwargs["summary"]
        assert summary == "Insert Svg lang (de,fr)"

        new_text = mock_deps.mw_page.edit.call_args.args[0]
        assert "{{Svg lang|dl=en|de|fr}}" in new_text

        assert title_info.steps.update_langs.details is not None
        assert title_info.steps.update_langs.details["newrevid"] == 999

    def test_update_langs_skipped_when_upload_skipped(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
        tmp_path,
    ):
        files_processor.config.upload = False
        files_processor.config.output_dir = tmp_path

        self._prepare_upload_success(mock_deps)
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "File:Main.svg")

        assert result is False
        assert title_info.steps.upload.msg == "skipped"
        assert title_info.steps.update_langs.result is None
        mock_deps.mw_page.edit.assert_not_called()

    def test_update_langs_no_text(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        self._prepare_upload_success(mock_deps)
        mock_deps.mw_page.get_text.return_value = ""
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.status == "success"
        assert title_info.steps.upload.result is True
        assert title_info.steps.update_langs.result is False
        assert title_info.error is None

    def test_update_langs_no_langs(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        self._prepare_upload_success(mock_deps)
        mock_deps.files_service.get_file_languages.return_value = FileLanguagesMap(langs=["en"])
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.status == "success"
        assert title_info.steps.update_langs.result is None
        assert title_info.steps.update_langs.msg == "Skipped - no languages found"
        mock_deps.mw_page.edit.assert_not_called()

    def test_update_langs_edit_failed(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        self._prepare_upload_success(mock_deps)
        mock_deps.mw_page.edit.return_value = {"success": False, "error": "ratelimited"}
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.status == "success"
        assert title_info.error is None
        assert title_info.steps.update_langs.result is False

        assert title_info.steps.update_langs.details is not None
        assert title_info.steps.update_langs.details["error"] == "ratelimited"

    def test_update_langs_exception_does_not_fail_file(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        self._prepare_upload_success(mock_deps)
        mock_deps.files_service.get_file_languages.side_effect = ValueError("API error")
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.status == "success"
        assert title_info.error is None
        assert title_info.steps.update_langs.result is False
        assert title_info.steps.update_langs.msg == "Error updating langs"

        assert title_info.steps.update_langs.details is not None
        assert "API error" in title_info.steps.update_langs.details["error"]

    def test_update_langs_load_langs_error(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        self._prepare_upload_success(mock_deps)
        mock_deps.files_service.get_file_languages.return_value = FileLanguagesMap(
            langs=None, error="Metadata not found for File:Test.svg"
        )
        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.status == "success"
        assert title_info.error is None
        assert title_info.steps.update_langs.result is False
        assert title_info.steps.update_langs.msg == "Could not load file languages"

        assert title_info.steps.update_langs.details is not None
        assert title_info.steps.update_langs.details["error"] == "Metadata not found for File:Test.svg"
        mock_deps.mw_page.edit.assert_not_called()

    def test_update_langs_prefixes_file_title(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        self._prepare_upload_success(mock_deps)
        title_info = FilesProcessedItem(title="Total daily covid deaths, Africa, Apr 13, 2024.svg")

        result = files_processor.process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.steps.update_langs.result is True

        used_title = mock_deps.mw_client_page.load.call_args.args[0]
        assert used_title == "File:Total daily covid deaths, Africa, Apr 13, 2024.svg"
        assert mock_deps.files_service.get_file_languages.call_args.args[0] == used_title

    def test_update_langs_identical(
        self,
        files_processor: OneFileProcessor,
        mock_deps,
    ):
        self._prepare_upload_success(mock_deps)
        original_text = "{{Information\n|other versions={{Svg lang|de|fr}}\n}}"
        mock_deps.mw_page.get_text.return_value = original_text

        files_processor.other_versions_updater.add_svg_langs = MagicMock(return_value=original_text)

        title_info = FilesProcessedItem(title="File:Test.svg")

        result = files_processor.process_one_item(title_info, "File:Main.svg")

        assert result is True
        assert title_info.steps.update_langs.msg == "Skipped - page content is already identical"

        assert title_info.steps.update_langs.result is None
        mock_deps.mw_page.edit.assert_not_called()
