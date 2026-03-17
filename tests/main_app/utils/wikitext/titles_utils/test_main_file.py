"""
Tests for src/main_app/utils/wikitext/titles_utils/main_file.py
"""

from __future__ import annotations

from src.main_app.utils.wikitext.titles_utils.main_file import (
    find_main_title_from_template,
    match_main_title_from_url,
    match_main_title_from_url_new,
)


class TestMatchMainTitleFromUrl:
    """Tests for the match_main_title_from_url function."""

    def test_match_url_basic(self) -> None:
        """Test matching a basic URL."""
        text = "*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg"
        result = match_main_title_from_url(text)
        assert result == "File:test.svg"

    def test_match_url_with_translation(self) -> None:
        """Test matching URL with 'Translation' variant."""
        text = "*'''Translation''': https://svgtranslate.toolforge.org/File:test.svg"
        result = match_main_title_from_url(text)
        assert result == "File:test.svg"

    def test_no_match(self) -> None:
        """Test when no URL pattern is found."""
        text = "Some text without a translate URL"
        result = match_main_title_from_url(text)
        assert result is None

    def test_match_url_with_complex_filename(self) -> None:
        """Test matching URL with complex filename."""
        text = "*'''Translate''': https://svgtranslate.toolforge.org/File:health-expenditure,World,2020.svg"
        result = match_main_title_from_url(text)
        assert result == "File:health-expenditure,World,2020.svg"

    def test_match_url_in_multiline_text(self) -> None:
        """Test matching URL in multiline text."""
        text = """Some other text
*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg
More text
"""
        result = match_main_title_from_url(text)
        assert result == "File:test.svg"

    def test_invalid_url_domain(self) -> None:
        """Test that URLs from other domains are not matched."""
        text = "*'''Translate''': https://example.org/File:test.svg"
        result = match_main_title_from_url(text)
        assert result is None

    def test_url_without_file_prefix(self) -> None:
        """Test URL without File: prefix is not matched."""
        text = "*'''Translate''': https://svgtranslate.toolforge.org/test.svg"
        result = match_main_title_from_url(text)
        assert result is None


class TestMatchMainTitleFromUrlNew:
    """Tests for the match_main_title_from_url_new function."""

    def test_match_url_basic(self) -> None:
        """Test matching a basic URL."""
        text = "*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg"
        result = match_main_title_from_url_new(text)
        assert result == "File:test.svg"

    def test_match_url_with_path_after_domain(self) -> None:
        """Test matching URL with full path."""
        text = "*'''Translate''': https://svgtranslate.toolforge.org/File:health-expenditure,World,2020.svg"
        result = match_main_title_from_url_new(text)
        assert result == "File:health-expenditure,World,2020.svg"

    def test_match_url_case_insensitive_domain(self) -> None:
        """Test matching URL with case-insensitive domain."""
        text = "*'''Translate''': https://SVGTRANSLATE.TOOLFORGE.ORG/File:test.svg"
        result = match_main_title_from_url_new(text)
        assert result == "File:test.svg"

    def test_match_url_with_trailing_characters(self) -> None:
        """Test matching URL with trailing characters like ] or )."""
        text = "*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg]"
        result = match_main_title_from_url_new(text)
        assert result == "File:test.svg"

    def test_match_url_in_wikilink(self) -> None:
        """Test matching URL inside a wikilink."""
        # The function extracts URL from the pattern, wikilink brackets are stripped
        text = "*'''Translate''': [[https://svgtranslate.toolforge.org/File:test.svg|link text]]"
        result = match_main_title_from_url_new(text)
        # The URL is extracted but the wikilink format causes the path to include the bracket
        # The actual behavior: the URL pattern doesn't match wikilink format
        assert result is None

    def test_no_match_wrong_domain(self) -> None:
        """Test that URLs from other domains are not matched."""
        text = "*'''Translate''': https://example.org/File:test.svg"
        result = match_main_title_from_url_new(text)
        assert result is None

    def test_no_match_non_svg_file(self) -> None:
        """Test that non-SVG files are not matched."""
        text = "*'''Translate''': https://svgtranslate.toolforge.org/test.png"
        result = match_main_title_from_url_new(text)
        assert result is None

    def test_no_match_empty_text(self) -> None:
        """Test with empty text."""
        result = match_main_title_from_url_new("")
        assert result is None

    def test_match_url_with_spaces_in_filename(self) -> None:
        """Test matching URL with spaces in filename."""
        # Spaces in URLs are typically encoded as %20
        text = "*'''Translate''': https://svgtranslate.toolforge.org/File:test%20file.svg"
        result = match_main_title_from_url_new(text)
        assert result == "File:test file.svg"

    def test_match_url_encoded_filename(self) -> None:
        """Test matching URL with URL-encoded filename."""
        text = "*'''Translate''': https://svgtranslate.toolforge.org/File:test%20file.svg"
        result = match_main_title_from_url_new(text)
        assert result == "File:test file.svg"

    def test_invalid_url_raises_value_error(self) -> None:
        """Test that invalid URL returns None due to ValueError."""
        # URL with invalid format that causes urlparse to raise ValueError
        # This tests the exception handler at lines 32-33
        text = "*'''Translate''': http://[invalid-url"
        result = match_main_title_from_url_new(text)
        assert result is None

    def test_wrong_domain_returns_none(self) -> None:
        """Test that URL with wrong domain returns None (line 36)."""
        text = "*'''Translate''': https://example.com/File:test.svg"
        result = match_main_title_from_url_new(text)
        assert result is None


class TestFindMainTitleFromTemplate:
    """Tests for the find_main_title_from_template function."""

    def test_extract_from_svglanguages(self) -> None:
        """Test extracting title from {{SVGLanguages}} template."""
        text = "{{SVGLanguages|test-file,World,2020.svg}}"
        result = find_main_title_from_template(text)
        assert result == "test-file,World,2020.svg"

    def test_extract_with_underscores_converted(self) -> None:
        """Test that underscores are converted to spaces."""
        text = "{{SVGLanguages|test_file_name.svg}}"
        result = find_main_title_from_template(text)
        assert result == "test file name.svg"

    def test_no_svglanguages_template(self) -> None:
        """Test when no {{SVGLanguages}} template exists."""
        text = "Some text without the template"
        result = find_main_title_from_template(text)
        assert result is None

    def test_case_insensitive_template_name(self) -> None:
        """Test that template name matching is case-insensitive."""
        text = "{{svglanguages|test.svg}}"
        result = find_main_title_from_template(text)
        assert result == "test.svg"

    def test_empty_text(self) -> None:
        """Test with empty text."""
        result = find_main_title_from_template("")
        assert result is None

    def test_whitespace_stripped(self) -> None:
        """Test that whitespace is stripped from the title."""
        text = "{{SVGLanguages|  test.svg  }}"
        result = find_main_title_from_template(text)
        assert result == "test.svg"
