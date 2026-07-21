"""Unit tests for add_lang_categories_to_owid_pages utils module."""

from __future__ import annotations

from src.main_app.jobs_workers.admin_jobs_workers.add_lang_categories_to_owid_pages.utils import (
    add_categories_to_text,
    build_category_lines,
    extract_svg_file_name,
    get_existing_lang_categories,
)


class TestExtractSvgFileName:
    """Tests for extract_svg_file_name function."""

    def test_extract_from_standard_translate_link(self):
        wikitext = "*'''Translate''': https://svgtranslate.toolforge.org/File:test_file.svg"
        assert extract_svg_file_name(wikitext) == "test_file.svg"

    def test_extract_from_translation_link(self):
        wikitext = "*'''Translation''': https://svgtranslate.toolforge.org/File:test_file.svg"
        assert extract_svg_file_name(wikitext) == "test_file.svg"

    def test_extract_from_translates_link(self):
        wikitext = "*'''Translates''': https://svgtranslate.toolforge.org/File:test_file.svg"
        assert extract_svg_file_name(wikitext) == "test_file.svg"

    def test_extract_with_underscores_and_commas(self):
        wikitext = (
            "*'''Translate''': https://svgtranslate.toolforge.org/File:share_with_mental_disorders,_World,_1990.svg"
        )
        assert extract_svg_file_name(wikitext) == "share_with_mental_disorders,_World,_1990.svg"

    def test_returns_none_when_no_translate_link(self):
        wikitext = "*'''Source''': https://ourworldindata.org/grapher/test"
        assert extract_svg_file_name(wikitext) is None

    def test_returns_none_for_empty_text(self):
        assert extract_svg_file_name("") is None

    def test_returns_none_for_non_svgtranslate_url(self):
        wikitext = "*'''Translate''': https://example.com/File:test.svg"
        assert extract_svg_file_name(wikitext) is None

    def test_extract_from_larger_wikitext(self):
        wikitext = """
{{owidslider
|start = 2021
|file = [[File:test.svg|link=|thumb|upright=1.6|test]]
}}
*'''Source''': https://ourworldindata.org/grapher/test
*'''Translate''': https://svgtranslate.toolforge.org/File:my_chart.svg
{{-}}
        """
        assert extract_svg_file_name(wikitext) == "my_chart.svg"


class TestBuildCategoryLines:
    """Tests for build_category_lines function."""

    def test_builds_categories_for_known_codes(self):
        result = build_category_lines(["en", "ar", "ja"])
        assert result == [
            "[[Category:English-language SVG]]",
            "[[Category:Arabic-language SVG]]",
            "[[Category:Japanese-language SVG]]",
        ]

    def test_skips_unknown_codes(self):
        result = build_category_lines(["en", "zzz_unknown", "ar"])
        assert result == [
            "[[Category:English-language SVG]]",
            "[[Category:Arabic-language SVG]]",
        ]

    def test_returns_empty_for_all_unknown_codes(self):
        result = build_category_lines(["zzz", "yyy"])
        assert result == []

    def test_returns_empty_for_empty_list(self):
        result = build_category_lines([])
        assert result == []

    def test_single_code(self):
        result = build_category_lines(["fr"])
        assert result == ["[[Category:French-language SVG]]"]


class TestGetExistingLangCategories:
    """Tests for get_existing_lang_categories function."""

    def test_finds_existing_categories(self):
        text = """
Some page content
[[Category:English-language SVG]]
[[Category:Japanese-language SVG]]
[[Category:Other category]]
        """
        result = get_existing_lang_categories(text)
        assert result == {
            "[[Category:English-language SVG]]",
            "[[Category:Japanese-language SVG]]",
        }

    def test_returns_empty_when_no_lang_categories(self):
        text = """
Some page content
[[Category:Other category]]
[[Category:Another category]]
        """
        assert get_existing_lang_categories(text) == set()

    def test_returns_empty_for_empty_text(self):
        assert get_existing_lang_categories("") == set()

    def test_case_insensitive_matching(self):
        text = "[[Category:english-language svg]]"
        result = get_existing_lang_categories(text)
        assert len(result) == 1


class TestAddCategoriesToText:
    """Tests for add_categories_to_text function."""

    def test_appends_categories_to_text(self):
        text = "Some page content"
        categories = ["[[Category:English-language SVG]]", "[[Category:Japanese-language SVG]]"]
        result = add_categories_to_text(text, categories)

        assert "[[Category:English-language SVG]]" in result
        assert "[[Category:Japanese-language SVG]]" in result
        assert result.startswith("Some page content\n")

    def test_appends_with_trailing_newline(self):
        text = "Some page content\n"
        categories = ["[[Category:English-language SVG]]"]
        result = add_categories_to_text(text, categories)

        assert result == "Some page content\n[[Category:English-language SVG]]\n"

    def test_returns_original_text_when_no_categories(self):
        text = "Some page content\n"
        result = add_categories_to_text(text, [])
        assert result == text

    def test_adds_newline_before_categories_if_missing(self):
        text = "content without trailing newline"
        categories = ["[[Category:English-language SVG]]"]
        result = add_categories_to_text(text, categories)

        assert result == "content without trailing newline\n[[Category:English-language SVG]]\n"

    def test_multiple_categories_on_separate_lines(self):
        text = "content\n"
        categories = [
            "[[Category:English-language SVG]]",
            "[[Category:Arabic-language SVG]]",
            "[[Category:Japanese-language SVG]]",
        ]
        result = add_categories_to_text(text, categories)

        expected = "content\n[[Category:English-language SVG]]\n[[Category:Arabic-language SVG]]\n[[Category:Japanese-language SVG]]\n"
        assert result == expected
