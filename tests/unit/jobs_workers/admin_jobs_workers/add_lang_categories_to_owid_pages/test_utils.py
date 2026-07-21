"""Unit tests for add_lang_categories_to_owid_pages utils module."""

from __future__ import annotations

from src.main_app.jobs_workers.admin_jobs_workers.add_lang_categories_to_owid_pages.utils import (
    build_category_names,
    extract_svg_file_name,
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


class TestBuildCategoryNames:
    """Tests for build_category_names function."""

    def test_builds_categories_for_known_codes(self):
        result = build_category_names(["en", "ar", "ja"])
        assert result == [
            "English-language SVG",
            "Arabic-language SVG",
            "Japanese-language SVG",
        ]

    def test_skips_unknown_codes(self):
        result = build_category_names(["en", "zzz_unknown", "ar"])
        assert result == [
            "English-language SVG",
            "Arabic-language SVG",
        ]

    def test_returns_empty_for_all_unknown_codes(self):
        result = build_category_names(["zzz", "yyy"])
        assert result == []

    def test_returns_empty_for_empty_list(self):
        result = build_category_names([])
        assert result == []

    def test_single_code(self):
        result = build_category_names(["fr"])
        assert result == ["French-language SVG"]
