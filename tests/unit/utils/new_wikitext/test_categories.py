from types import SimpleNamespace

import pytest
import wikitextparser as wtp

from src.main_app.utils.new_wikitext.categories import CategoryExtractor, CategoryLink, CategoryMerger


def _wtp_works() -> bool:
    try:
        wtp.parse("a")
    except RuntimeError:
        return False
    return True


needs_wtp = pytest.mark.skipif(not _wtp_works(), reason="real wikitextparser is required")


def _cat(target: str) -> CategoryLink:
    return CategoryLink(link=SimpleNamespace(string=f"[[{target}]]"), target=target)


class FakeExtractor:
    """Returns prepared categories for each text."""

    def __init__(self, by_text):
        self.by_text = by_text

    def extract_categories(self, text):
        return self.by_text[text]


class TestCategoryExtractorCapitalize:
    """Tests for ``CategoryExtractor.capitalize_category``."""

    def test_capitalizes_both_parts(self):
        assert CategoryExtractor().capitalize_category("category:foo bar") == "Category:Foo bar"

    def test_without_colon_is_unchanged(self):
        assert CategoryExtractor().capitalize_category("nocolon") == "nocolon"


@needs_wtp
class TestCategoryExtractorExtract:
    """Tests for ``CategoryExtractor.extract_categories``."""

    def test_extracts_only_categories(self):
        cats = CategoryExtractor().extract_categories("[[Category:a_b]] [[File:x.svg]]")
        assert [c.target for c in cats] == ["Category:A b"]

    def test_non_string_returns_empty_list(self):
        assert CategoryExtractor().extract_categories(None) == []


class TestCategoryMergerFindMissing:
    """Tests for ``CategoryMerger.find_missing_categories``."""

    def test_returns_only_missing(self):
        missing = CategoryMerger().find_missing_categories(
            [_cat("Category:A")], [_cat("Category:A"), _cat("Category:B")]
        )
        assert [c.target for c in missing] == ["Category:B"]

    def test_empty_target_returns_base(self):
        base = [_cat("Category:A")]
        assert CategoryMerger().find_missing_categories([], base) == base


class TestCategoryMergerMerge:
    """Tests for ``CategoryMerger.merge_categories`` with a fake extractor."""

    def test_appends_missing_categories(self):
        fake = FakeExtractor({"old": [_cat("Category:A")], "new": []})
        assert CategoryMerger(extractor=fake).merge_categories("old", "new") == "new\n[[Category:A]]"

    def test_returns_new_text_when_nothing_missing(self):
        fake = FakeExtractor({"old": [_cat("Category:A")], "new": [_cat("Category:A")]})
        assert CategoryMerger(extractor=fake).merge_categories("old", "new") == "new"

    def test_empty_old_text_returns_new_text(self):
        assert CategoryMerger().merge_categories("", "new") == "new"


class TestCategoryMergerMergeIntoText:
    """Tests for ``CategoryMerger.merge_categories_into_text``."""

    def test_empty_text_is_unchanged(self):
        assert CategoryMerger().merge_categories_into_text(["Category:A"], "") == ""

    def test_adds_all_when_text_has_no_categories(self):
        fake = FakeExtractor({"text": []})
        result = CategoryMerger(extractor=fake).merge_categories_into_text(["Category:A"], "text")
        assert result == "text\n[[Category:A]]"


@needs_wtp
class TestCategoryMergerSort:
    """Tests for ``CategoryMerger.sort_categories``."""

    def test_moves_sorted_categories_to_end(self):
        result = CategoryMerger().sort_categories("text [[Category:B]] [[Category:A]]")
        assert result == "text\n\n[[Category:A]]\n[[Category:B]]"

    def test_without_categories_is_unchanged(self):
        assert CategoryMerger().sort_categories("text") == "text"
