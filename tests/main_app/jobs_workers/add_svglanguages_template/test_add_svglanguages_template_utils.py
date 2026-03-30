"""Unit tests for add_svglanguages_template utils module."""

from __future__ import annotations

import pytest

from src.main_app.jobs_workers.add_svglanguages_template.utils import (
    RE_SVG_LANG,
    RE_TRANSLATE,
    add_template_to_text,
    load_link_file_name,
)


class TestLoadLinkFileName:
    """Tests for load_link_file_name function."""

    def test_extract_file_name_from_translate_link(self):
        """Test extracting file name from standard Translate link."""
        wikitext = """
*[[Commons:List of interactive graphs|Return to list]]

{{owidslider
|start        = 2021
|list         = Template:OWID/share with mental and substance disorders#gallery
|location      = commons
|caption      =
|title        =
|language     =
|file         = [[File:share with mental and substance disorders, World, 2021 (cropped).svg|link=|thumb|upright=1.6|share with mental and substance disorders]]
|startingView = World
}}
*'''Source''': https://ourworldindata.org/grapher/share-with-mental-and-substance-disorders
*'''Translate''': https://svgtranslate.toolforge.org/File:share_with_mental_and_substance_disorders,_World,_1990.svg
{{-}}
        """

        file_name = load_link_file_name(wikitext)
        assert file_name == "share_with_mental_and_substance_disorders,_World,_1990.svg"

    def test_extract_file_name_with_spaces_in_url(self):
        """Test extracting file name when URL has spaces."""
        wikitext = "*'''Translate''': https://svgtranslate.toolforge.org/File:health-expenditure-government-expenditure,World,2000.svg"

        file_name = load_link_file_name(wikitext)
        assert file_name == "health-expenditure-government-expenditure,World,2000.svg"

    def test_extract_file_name_with_extra_whitespace(self):
        """Test extracting file name with extra whitespace around the link."""
        wikitext = "*'''Translate''':   https://svgtranslate.toolforge.org/File:test-file.svg   \n"

        file_name = load_link_file_name(wikitext)
        assert file_name == "test-file.svg"

    def test_returns_none_when_no_translate_link(self):
        """Test that None is returned when no Translate link exists."""
        wikitext = """
{{owidslider
|start = 2021
|file = [[File:test.svg|link=|thumb|upright=1.6|test]]
}}
*'''Source''': https://ourworldindata.org/grapher/test
        """

        file_name = load_link_file_name(wikitext)
        assert file_name is None

    def test_returns_none_when_empty_text(self):
        """Test that None is returned for empty text."""
        assert load_link_file_name("") is None

    def test_translate_link_with_typo(self):
        """Test that Translate link with typo (Translat) is NOT matched since regex requires word chars."""
        # The regex requires at least one word character after "Translat"
        wikitext = "*'''Translat''': https://svgtranslate.toolforge.org/File:test-file.svg"

        file_name = load_link_file_name(wikitext)
        # This should return None because "Translat" alone doesn't match the pattern
        assert file_name is None

    def test_translate_link_variations(self):
        """Test various Translate link format variations."""
        test_cases = [
            ("*'''Translate''': https://svgtranslate.toolforge.org/File:a.svg", "a.svg"),
            ("*'''Translates''': https://svgtranslate.toolforge.org/File:b.svg", "b.svg"),
            ("*'''Translation''': https://svgtranslate.toolforge.org/File:c.svg", "c.svg"),
        ]

        for wikitext, expected in test_cases:
            assert load_link_file_name(wikitext) == expected


class TestAddTemplateToText:
    """Tests for add_template_to_text function."""

    def test_add_template_after_translate_link(self):
        """Test adding template text after Translate link."""
        text = """*'''Source''': https://example.org
*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg
Some other content
"""
        template_text = "{{SVGLanguages|test.svg}}"

        result = add_template_to_text(text, template_text)

        assert "{{SVGLanguages|test.svg}}" in result
        assert "*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg" in result
        # Template should be added on a new line after Translate
        assert "*{{SVGLanguages|test.svg}}" in result or "\n*{{SVGLanguages|test.svg}}" in result

    def test_returns_original_text_when_no_translate_link(self):
        """Test that original text is returned when no Translate link exists."""
        text = """
{{owidslider
|start = 2021
}}
Some content without translate link
"""
        template_text = "{{SVGLanguages|test.svg}}"

        result = add_template_to_text(text, template_text)
        assert result == text
        assert "{{SVGLanguages|test.svg}}" not in result

    def test_adds_template_only_once(self):
        """Test that template is added only once even with multiple Translate-like patterns."""
        text = """*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg
*'''Translate''': https://svgtranslate.toolforge.org/File:test2.svg
"""
        template_text = "{{SVGLanguages|test.svg}}"

        result = add_template_to_text(text, template_text)

        # Should only add once (count=1 in re.sub)
        assert result.count("{{SVGLanguages|test.svg}}") == 1

    def test_template_added_with_proper_formatting(self):
        """Test that template is added with proper wikitext formatting."""
        text = "*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg\n"
        template_text = "{{SVGLanguages|test.svg}}"

        result = add_template_to_text(text, template_text)

        # Should have the original line plus the template on a new line starting with *
        lines = result.split("\n")
        translate_line_found = False
        template_line_found = False

        for line in lines:
            if "*'''Translate''':" in line:
                translate_line_found = True
            if line.startswith("*{{SVGLanguages|"):
                template_line_found = True

        assert translate_line_found
        assert template_line_found


class TestRE_SVG_LANG:
    """Tests for RE_SVG_LANG regex pattern."""

    def test_matches_standard_svglanguages_template(self):
        """Test matching standard SVGLanguages template."""
        text = "{{SVGLanguages|test-file.svg}}"
        match = RE_SVG_LANG.search(text)
        assert match is not None
        assert match.group(1).strip() == "test-file.svg"

    def test_matches_with_spaces_around_pipe(self):
        """Test matching with spaces around the pipe character."""
        text = "{{SVGLanguages | test-file.svg }}"
        match = RE_SVG_LANG.search(text)
        assert match is not None
        assert match.group(1).strip() == "test-file.svg"

    def test_matches_case_insensitive(self):
        """Test case-insensitive matching."""
        test_cases = [
            "{{SVGLanguages|test.svg}}",
            "{{svglanguages|test.svg}}",
            "{{SvgLanguages|test.svg}}",
            "{{SVGLANGUAGES|test.svg}}",
        ]

        for text in test_cases:
            match = RE_SVG_LANG.search(text)
            assert match is not None, f"Failed to match: {text}"

    def test_does_not_match_other_templates(self):
        """Test that other templates are not matched."""
        text = "{{OtherTemplate|test.svg}}"
        match = RE_SVG_LANG.search(text)
        assert match is None

    def test_matches_in_larger_text(self):
        """Test matching SVGLanguages within larger wikitext."""
        text = """
{{owidslider
|start = 2021
}}
{{SVGLanguages|complex-file-name,_World,_2020.svg}}
Some other content
"""
        match = RE_SVG_LANG.search(text)
        assert match is not None
        assert "complex-file-name,_World,_2020.svg" in match.group(1)


class TestRE_TRANSLATE:
    """Tests for RE_TRANSLATE regex pattern."""

    def test_matches_standard_translate_link(self):
        """Test matching standard Translate link."""
        text = "*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg"
        match = RE_TRANSLATE.search(text)
        assert match is not None
        assert match.group(1).strip() == "test.svg"

    def test_matches_with_extra_spaces(self):
        """Test matching with extra spaces."""
        text = "*  '''Translate''':   https://svgtranslate.toolforge.org/File:test.svg  "
        match = RE_TRANSLATE.search(text)
        assert match is not None
        assert match.group(1).strip() == "test.svg"

    def test_matches_case_insensitive(self):
        """Test case-insensitive matching."""
        test_cases = [
            "*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg",
            "*'''translate''': https://svgtranslate.toolforge.org/File:test.svg",
            "*'''TRANSLATE''': https://svgtranslate.toolforge.org/File:test.svg",
        ]

        for text in test_cases:
            match = RE_TRANSLATE.search(text)
            assert match is not None, f"Failed to match: {text}"

    def test_matches_translate_variations(self):
        """Test matching variations like Translates, Translation."""
        text = "*'''Translates''': https://svgtranslate.toolforge.org/File:test.svg"
        match = RE_TRANSLATE.search(text)
        assert match is not None

    def test_does_not_match_other_urls(self):
        """Test that other URLs are not matched."""
        text = "*'''Source''': https://ourworldindata.org/grapher/test"
        match = RE_TRANSLATE.search(text)
        assert match is None

    def test_does_not_match_non_svgtranslate_domain(self):
        """Test that non-svgtranslate domains are not matched."""
        text = "*'''Translate''': https://example.com/File:test.svg"
        match = RE_TRANSLATE.search(text)
        assert match is None
