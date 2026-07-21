"""Unit tests for add_lang_categories_to_owid_pages worker module."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from src.main_app.jobs_workers.admin_jobs_workers.add_lang_categories_to_owid_pages.worker import (
    AddLangCategoriesWorker,
    PageInfo,
)


@pytest.fixture
def mock_lang_worker(mock_base_worker, mock_before_run) -> AddLangCategoriesWorker:
    worker = AddLangCategoriesWorker(job_id=1, user=None)
    worker.site = mock_base_worker["get_user_site"]
    return worker


# ── PageInfo dataclass ─────────────────────────────────────────────────────


class TestPageInfo:
    def test_page_info_initialization(self):
        info = PageInfo(page_title="OWID/test_page")

        assert info.page_title == "OWID/test_page"
        assert info.svg_file is None
        assert info.lang_codes == []
        assert info.categories_added == []
        assert info.status == "pending"
        assert info.error is None
        assert info._text is None
        assert info._categories == []

    def test_page_info_steps_initialized(self):
        info = PageInfo(page_title="OWID/test_page")

        expected_steps = [
            "load_page_text",
            "extract_file_name",
            "get_languages",
            "build_categories",
            "check_existing",
            "save_page",
        ]
        for step in expected_steps:
            assert step in info.steps
            assert info.steps[step]["result"] is None
            assert info.steps[step]["msg"] == ""

    def test_page_info_to_dict(self):
        info = PageInfo(page_title="OWID/test_page")
        info.status = "completed"
        info.svg_file = "test.svg"
        info.lang_codes = ["en", "ar"]
        info.categories_added = ["[[Category:English-language SVG]]"]

        result = info.to_dict()

        assert result["page_title"] == "OWID/test_page"
        assert result["svg_file"] == "test.svg"
        assert result["lang_codes"] == ["en", "ar"]
        assert result["categories_added"] == ["[[Category:English-language SVG]]"]
        assert result["status"] == "completed"
        assert "steps" in result
        assert "timestamp" in result


# ── Worker initialization ──────────────────────────────────────────────────


class TestWorkerInit:
    def test_worker_initialization(self):
        user = {"username": "test_user"}
        cancel_event = threading.Event()

        worker = AddLangCategoriesWorker(job_id=1, user=user, cancel_event=cancel_event)

        assert worker.job_id == 1
        assert worker.user == user
        assert worker.cancel_event == cancel_event
        assert worker.site is None

    def test_get_job_type(self):
        worker = AddLangCategoriesWorker(job_id=1, user=None)
        assert worker.get_job_type() == "add_lang_categories_to_owid_pages"

    def test_reads_limit_items_from_args(self):
        worker = AddLangCategoriesWorker(job_id=1, user=None, args={"limit_items": 5})
        assert worker.limit_items == 5

    def test_defaults_limit_items_to_zero(self):
        worker = AddLangCategoriesWorker(job_id=1, user=None, args=None)
        assert worker.limit_items == 0

    def test_limit_items_zero_when_key_missing(self):
        worker = AddLangCategoriesWorker(job_id=1, user=None, args={"other_key": "value"})
        assert worker.limit_items == 0

    def test_initial_result_structure(self):
        worker = AddLangCategoriesWorker(job_id=1, user=None)
        result = worker.result

        assert result.status == "pending"
        assert result.summary.total == 0
        assert result.summary.processed == 0
        assert result.summary.success == 0
        assert result.summary.failed == 0
        assert result.summary.skipped == 0
        assert result.summary.no_file == 0


# ── Step: load_page_text ───────────────────────────────────────────────────


class TestStepLoadPageText:
    def test_success(self, mock_lang_worker):
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Some page content"

        info = PageInfo(page_title="OWID/test")
        result = mock_lang_worker._step_load_page_text(info, mock_page)

        assert result is True
        assert info._text == "Some page content"
        assert info.steps["load_page_text"]["result"] is True

    def test_failure_on_empty_text(self, mock_lang_worker):
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""

        info = PageInfo(page_title="OWID/test")
        result = mock_lang_worker._step_load_page_text(info, mock_page)

        assert result is False
        assert info.status == "failed"
        assert info.steps["load_page_text"]["result"] is False


# ── Step: extract_file_name ────────────────────────────────────────────────


class TestStepExtractFileName:
    def test_success(self, mock_lang_worker):
        info = PageInfo(page_title="OWID/test")
        info._text = "*'''Translate''': https://svgtranslate.toolforge.org/File:test_chart.svg"

        result = mock_lang_worker._step_extract_file_name(info)

        assert result is True
        assert info.svg_file == "test_chart.svg"
        assert info.steps["extract_file_name"]["result"] is True

    def test_failure_no_translate_link(self, mock_lang_worker):
        info = PageInfo(page_title="OWID/test")
        info._text = "Some content without translate link"

        result = mock_lang_worker._step_extract_file_name(info)

        assert result is False
        assert info.status == "failed"
        assert mock_lang_worker.result.summary.no_file == 1


# ── Step: get_languages ────────────────────────────────────────────────────


class TestStepGetLanguages:
    def test_success(self, mock_lang_worker, mock_lang_categories_services):
        mock_lang_categories_services["get_file_languages"].return_value = {
            "error": None,
            "langs": ["en", "ja"],
        }

        info = PageInfo(page_title="OWID/test")
        info.svg_file = "test.svg"

        result = mock_lang_worker._step_get_languages(info)

        assert result is True
        assert info.lang_codes == ["en", "ja"]

    def test_failure_on_api_error(self, mock_lang_worker, mock_lang_categories_services):
        mock_lang_categories_services["get_file_languages"].return_value = {
            "error": "API error: timeout",
            "langs": None,
        }

        info = PageInfo(page_title="OWID/test")
        info.svg_file = "test.svg"

        result = mock_lang_worker._step_get_languages(info)

        assert result is False
        assert info.status == "failed"
        assert "API error" in info.error

    def test_failure_on_empty_langs(self, mock_lang_worker, mock_lang_categories_services):
        mock_lang_categories_services["get_file_languages"].return_value = {
            "error": None,
            "langs": None,
        }

        info = PageInfo(page_title="OWID/test")
        info.svg_file = "test.svg"

        result = mock_lang_worker._step_get_languages(info)

        assert result is False


# ── Step: build_categories ────────────────────────────────────────────────


class TestStepBuildCategories:
    def test_success(self, mock_lang_worker):
        info = PageInfo(page_title="OWID/test")
        info.lang_codes = ["en", "ar"]

        result = mock_lang_worker._step_build_categories(info)

        assert result is True
        # build_category_names returns "Category:XXX" (no [[...]] wrapper)
        assert "Category:English-language SVG" in info._categories
        assert "Category:Arabic-language SVG" in info._categories
        assert not any("[[Category:" in c for c in info._categories)

    def test_failure_on_no_recognised_codes(self, mock_lang_worker):
        info = PageInfo(page_title="OWID/test")
        info.lang_codes = ["zzz_unknown"]

        result = mock_lang_worker._step_build_categories(info)

        assert result is False
        assert info.status == "failed"

    def test_failure_on_empty_codes(self, mock_lang_worker):
        info = PageInfo(page_title="OWID/test")
        info.lang_codes = []

        result = mock_lang_worker._step_build_categories(info)

        assert result is False


# ── Step: check_existing ──────────────────────────────────────────────────


class TestStepCheckExisting:
    def test_all_categories_are_new_with_existing_cats_on_page(self, mock_lang_worker):
        """Page has categories but none match candidates — all are added via merge_categories_into_text."""
        info = PageInfo(page_title="OWID/test")
        info._text = "Content\n[[Category:Other category]]"
        info._new_text = "Category:English-language SVG\nCategory:Japanese-language SVG"

        result = mock_lang_worker._step_check_existing(info)

        assert len(result) == 2
        assert "[[Category:English-language SVG]]" in result
        assert "[[Category:Japanese-language SVG]]" in result
        # _new_text should now contain the merged result
        assert "[[Category:English-language SVG]]" in (info._new_text or "")
        assert "[[Category:Japanese-language SVG]]" in (info._new_text or "")

    def test_all_categories_are_new_no_existing_cats_fallback(self, mock_lang_worker):
        """Page has no categories — triggers the manual-append fallback."""
        info = PageInfo(page_title="OWID/test")
        info._text = "Some page content without categories"
        info._new_text = "Category:English-language SVG\nCategory:Japanese-language SVG"

        result = mock_lang_worker._step_check_existing(info)

        assert len(result) == 2
        assert "[[Category:English-language SVG]]" in result
        assert "[[Category:Japanese-language SVG]]" in result
        assert "[[Category:English-language SVG]]" in (info._new_text or "")

    def test_some_categories_already_exist(self, mock_lang_worker):
        """Page already has one candidate — only the missing one is returned."""
        info = PageInfo(page_title="OWID/test")
        info._text = "Content\n[[Category:English-language SVG]]"
        info._new_text = "Category:English-language SVG\nCategory:Japanese-language SVG"

        result = mock_lang_worker._step_check_existing(info)

        assert len(result) == 1
        assert "[[Category:Japanese-language SVG]]" in result
        # English should not be duplicated in merged text
        assert (info._new_text or "").count("[[Category:English-language SVG]]") == 1

    def test_all_categories_already_exist(self, mock_lang_worker):
        """All candidates present — returns empty list, marks as skipped."""
        info = PageInfo(page_title="OWID/test")
        info._text = "Content\n[[Category:English-language SVG]]\n[[Category:Japanese-language SVG]]"
        info._new_text = "Category:English-language SVG\nCategory:Japanese-language SVG"

        result = mock_lang_worker._step_check_existing(info)

        assert result == []
        assert info.status == "skipped"


# ── Step: save_page ───────────────────────────────────────────────────────


class TestStepSavePage:
    def test_success(self, mock_lang_worker):
        mock_page = MagicMock()
        mock_page.edit.return_value = {"success": True, "newrevid": 12345}

        info = PageInfo(page_title="OWID/test")
        # _new_text is the already-merged result from _step_check_existing
        info._new_text = "original\n[[Category:English-language SVG]]"
        new_cats = ["[[Category:English-language SVG]]"]

        result = mock_lang_worker._step_save_page(info, mock_page, new_cats)

        assert result is True
        assert mock_lang_worker.result.summary.success == 1
        assert info.steps["save_page"]["result"] is True
        mock_page.edit.assert_called_once()
        # Verify the merged text was passed to edit
        call_args = mock_page.edit.call_args
        assert call_args[0][0] == "original\n[[Category:English-language SVG]]"

    def test_failure(self, mock_lang_worker):
        mock_page = MagicMock()
        mock_page.edit.return_value = {"success": False, "error": "API error"}

        info = PageInfo(page_title="OWID/test")
        info._new_text = "original\n[[Category:English-language SVG]]"
        new_cats = ["[[Category:English-language SVG]]"]

        result = mock_lang_worker._step_save_page(info, mock_page, new_cats)

        assert result is False
        assert info.status == "failed"
        assert info.error == "API error"


# ── _process_one_item ─────────────────────────────────────────────────────


class TestProcessOneItem:
    def test_success_flow(self, mock_lang_worker, mock_lang_categories_services):
        mock_page = MagicMock()

        def mock_load(info, page):
            info._text = "*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg"
            return True

        def mock_extract(info):
            info.svg_file = "test.svg"
            return True

        def mock_get_langs(info):
            info.lang_codes = ["en", "ar"]
            return True

        def mock_build(info):
            info._new_text = "Category:English-language SVG\nCategory:Arabic-language SVG"
            return True

        mock_lang_worker._step_load_page_text = MagicMock(side_effect=mock_load)
        mock_lang_worker._step_extract_file_name = MagicMock(side_effect=mock_extract)
        mock_lang_worker._step_get_languages = MagicMock(side_effect=mock_get_langs)
        mock_lang_worker._step_build_categories = MagicMock(side_effect=mock_build)
        mock_lang_worker._step_check_existing = MagicMock(
            return_value=["[[Category:English-language SVG]]", "[[Category:Arabic-language SVG]]"]
        )
        mock_lang_worker._step_save_page = MagicMock(return_value=True)

        result = mock_lang_worker._process_one_item("OWID/test")

        assert result is True
        assert mock_lang_worker.result.summary.processed == 1

    def test_stops_on_load_failure(self, mock_lang_worker):
        mock_lang_worker._step_load_page_text = MagicMock(return_value=False)
        mock_lang_worker._step_extract_file_name = MagicMock()
        mock_lang_worker._step_get_languages = MagicMock()

        result = mock_lang_worker._process_one_item("OWID/test")

        assert result is False
        mock_lang_worker._step_extract_file_name.assert_not_called()
        mock_lang_worker._step_get_languages.assert_not_called()

    def test_stops_on_extract_failure(self, mock_lang_worker):
        def mock_load(info, page):
            info._text = "no translate link"
            return True

        mock_lang_worker._step_load_page_text = MagicMock(side_effect=mock_load)
        mock_lang_worker._step_extract_file_name = MagicMock(return_value=False)
        mock_lang_worker._step_get_languages = MagicMock()

        result = mock_lang_worker._process_one_item("OWID/test")

        assert result is False
        mock_lang_worker._step_get_languages.assert_not_called()

    def test_skipped_when_no_new_categories(self, mock_lang_worker):
        def mock_load(info, page):
            info._text = "text"
            return True

        def mock_extract(info):
            info.svg_file = "test.svg"
            return True

        def mock_get_langs(info):
            info.lang_codes = ["en"]
            return True

        def mock_build(info):
            info._new_text = "Category:English-language SVG"
            return True

        mock_lang_worker._step_load_page_text = MagicMock(side_effect=mock_load)
        mock_lang_worker._step_extract_file_name = MagicMock(side_effect=mock_extract)
        mock_lang_worker._step_get_languages = MagicMock(side_effect=mock_get_langs)
        mock_lang_worker._step_build_categories = MagicMock(side_effect=mock_build)
        mock_lang_worker._step_check_existing = MagicMock(return_value=[])
        mock_lang_worker._step_save_page = MagicMock()

        result = mock_lang_worker._process_one_item("OWID/test")

        assert result is False
        mock_lang_worker._step_save_page.assert_not_called()


# ── process() ─────────────────────────────────────────────────────────────


class TestProcess:
    def test_process_success(self, mock_lang_categories_services, mock_site, monkeypatch: pytest.MonkeyPatch):
        mock_lang_categories_services["get_user_site"].return_value = mock_site

        mock_page = MagicMock()
        mock_page.name = "OWID/test_page"
        mock_site.allpages.return_value = [mock_page]

        worker = AddLangCategoriesWorker(job_id=1, user={"username": "test"})
        worker._process_one_item = MagicMock(return_value=True)

        result = worker.run()

        assert result["status"] == "completed"
        assert result["summary"]["total"] == 1

    def test_process_fails_without_site(self, mock_lang_categories_services, monkeypatch: pytest.MonkeyPatch):
        mock_lang_categories_services["get_user_site"].return_value = None

        worker = AddLangCategoriesWorker(job_id=1, user=None)
        result = worker.run()

        assert result["status"] == "failed"
        assert result["failed_at"] is not None

    def test_process_respects_limit(self, mock_lang_categories_services, mock_site, monkeypatch: pytest.MonkeyPatch):
        mock_lang_categories_services["get_user_site"].return_value = mock_site

        mock_pages = [MagicMock(name=f"OWID/page{i}") for i in range(10)]
        for i, p in enumerate(mock_pages):
            p.name = f"OWID/page{i}"
        mock_site.allpages.return_value = mock_pages

        worker = AddLangCategoriesWorker(job_id=1, user={"username": "test"}, args={"limit_items": 3})
        worker._process_one_item = MagicMock(return_value=True)

        result = worker.run()

        assert result["summary"]["total"] == 3
        assert worker._process_one_item.call_count == 3

    def test_process_handles_cancellation(
        self, mock_lang_categories_services, mock_site, monkeypatch: pytest.MonkeyPatch
    ):
        mock_lang_categories_services["get_user_site"].return_value = mock_site

        mock_pages = [MagicMock(name=f"OWID/page{i}") for i in range(5)]
        for i, p in enumerate(mock_pages):
            p.name = f"OWID/page{i}"
        mock_site.allpages.return_value = mock_pages

        cancel_event = threading.Event()
        worker = AddLangCategoriesWorker(job_id=1, user={"username": "test"}, cancel_event=cancel_event)

        call_count = [0]

        def mock_process_one(title):
            call_count[0] += 1
            if call_count[0] == 1:
                cancel_event.set()

        worker._process_one_item = mock_process_one  # type: ignore

        worker.process()

        assert call_count[0] == 1
