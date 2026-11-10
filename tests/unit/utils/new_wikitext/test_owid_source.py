from __future__ import annotations

import unittest.mock as mock

from src.main_app.utils.new_wikitext.owid_source import OwidSourceFinder

SOURCE_LINE = "*'''Source''': https://ourworldindata.org/grapher/foo-bar]\n"


class TestOwidSourceFinderCheckUrl:
    """Tests for ``OwidSourceFinder.check_url``."""

    def test_accepts_owid_hosts(self):
        assert OwidSourceFinder.check_url("https://www.ourworldindata.org/x") is True

    def test_rejects_other_hosts(self):
        assert OwidSourceFinder.check_url("https://example.org/x") is False

    def test_rejects_invalid_url(self):
        assert OwidSourceFinder.check_url("http://[bad") is False


class TestOwidSourceFinderFind:
    """Tests for ``OwidSourceFinder.find_template_source``."""

    def test_finds_source_line_and_strips_trailing_chars(self):
        assert OwidSourceFinder.find_template_source(SOURCE_LINE) == "https://ourworldindata.org/grapher/foo-bar"

    def test_finds_bullet_line(self):
        text = "* https://ourworldindata.org/grapher/baz\n"
        assert OwidSourceFinder.find_template_source(text) == "https://ourworldindata.org/grapher/baz"

    def test_requires_grapher_by_default(self):
        text = "* https://ourworldindata.org/explorers/x\n"
        finder = OwidSourceFinder()
        assert finder.find_template_source(text) == ""
        assert finder.find_template_source(text, check_grapher=False) == "https://ourworldindata.org/explorers/x"

    def test_returns_empty_when_missing(self):
        assert OwidSourceFinder.find_template_source("nothing") == ""


class TestFindTemplateSource:
    def test_basic(self):
        wikitext = """
        *'''Source''': https://ourworldindata.org/grapher/share-electricity-renewables
        *'''Translate''': https://svgtranslate.toolforge.org/File:Share_electricity_renewables,_World,_1985.svg
        """
        expected = "https://ourworldindata.org/grapher/share-electricity-renewables"
        assert OwidSourceFinder.find_from_source_line(wikitext) == expected

    def test_with_www(self):
        wikitext = "*'''Source''': https://www.ourworldindata.org/grapher/co2-emissions"
        expected = "https://www.ourworldindata.org/grapher/co2-emissions"
        assert OwidSourceFinder.find_from_source_line(wikitext) == expected

    def test_http_scheme(self):
        wikitext = "*'''Source''': http://ourworldindata.org/grapher/co2-emissions"
        expected = "http://ourworldindata.org/grapher/co2-emissions"
        assert OwidSourceFinder.find_from_source_line(wikitext) == expected

    def test_trailing_characters(self):
        wikitext = "*'''Source''': https://ourworldindata.org/grapher/life-expectancy]]"
        expected = "https://ourworldindata.org/grapher/life-expectancy"
        assert OwidSourceFinder.find_from_source_line(wikitext) == expected

    def test_extra_spaces(self):
        wikitext = "*'''Source''':     https://ourworldindata.org/grapher/gdp-per-capita"
        expected = "https://ourworldindata.org/grapher/gdp-per-capita"
        assert OwidSourceFinder.find_from_source_line(wikitext) == expected

    def test_case_insensitive_source(self):
        wikitext = "*'''SOURCE''': https://ourworldindata.org/grapher/energy-consumption"
        expected = "https://ourworldindata.org/grapher/energy-consumption"
        assert OwidSourceFinder.find_from_source_line(wikitext) == expected

    def test_multiple_lines(self):
        wikitext = """
        some text
        *'''Source''': https://ourworldindata.org/grapher/child-mortality
        more text
        """
        expected = "https://ourworldindata.org/grapher/child-mortality"
        assert OwidSourceFinder.find_from_source_line(wikitext) == expected

    def test_invalid_domain(self):
        wikitext = "*'''Source''': https://example.org/data"
        assert OwidSourceFinder.find_from_source_line(wikitext) == ""

    def test_missing_source(self):
        wikitext = "*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg"
        assert OwidSourceFinder.find_from_source_line(wikitext) == ""

    def test_with_wikilink_brackets(self):
        wikitext = "*'''Source''': [https://ourworldindata.org/grapher/population-growth]"
        assert OwidSourceFinder.find_from_source_line(wikitext) == ""


class TestFindTemplateSource2:
    def test_basic_http(self):
        wikitext = """
        * http://ourworldindata.org/grapher/share-electricity-renewables
        """
        expected = "http://ourworldindata.org/grapher/share-electricity-renewables"
        assert OwidSourceFinder.find_from_bullet_line(wikitext) == expected

    def test_https(self):
        wikitext = "* https://ourworldindata.org/grapher/co2-emissions"
        expected = "https://ourworldindata.org/grapher/co2-emissions"
        assert OwidSourceFinder.find_from_bullet_line(wikitext) == expected

    def test_with_www(self):
        wikitext = "* https://www.ourworldindata.org/grapher/population"
        expected = "https://www.ourworldindata.org/grapher/population"
        assert OwidSourceFinder.find_from_bullet_line(wikitext) == expected

    def test_spaces_before_star(self):
        wikitext = "      * https://ourworldindata.org/grapher/gdp-per-capita"
        expected = "https://ourworldindata.org/grapher/gdp-per-capita"
        assert OwidSourceFinder.find_from_bullet_line(wikitext) == expected

    def test_spaces_after_star(self):
        wikitext = "*     https://ourworldindata.org/grapher/life-expectancy"
        expected = "https://ourworldindata.org/grapher/life-expectancy"
        assert OwidSourceFinder.find_from_bullet_line(wikitext) == expected

    def test_wikilink_brackets(self):
        wikitext = "* [https://ourworldindata.org/grapher/child-mortality]"
        assert OwidSourceFinder.find_from_bullet_line(wikitext) == ""

    def test_trailing_characters(self):
        wikitext = "* https://ourworldindata.org/grapher/fertility-rate]]"
        expected = "https://ourworldindata.org/grapher/fertility-rate"
        assert OwidSourceFinder.find_from_bullet_line(wikitext) == expected

    def test_invalid_domain(self):
        wikitext = "* https://example.org/data"
        assert OwidSourceFinder.find_from_bullet_line(wikitext) == ""

    def test_no_url(self):
        wikitext = "* some text without a url"
        assert OwidSourceFinder.find_from_bullet_line(wikitext) == ""

    def test_url_not_first_in_line(self):
        wikitext = "* source https://ourworldindata.org/grapher/test"
        assert OwidSourceFinder.find_from_bullet_line(wikitext) == ""

    def test_multiple_lines(self):
        wikitext = """
        text
        * https://ourworldindata.org/grapher/energy-consumption
        another line
        """
        expected = "https://ourworldindata.org/grapher/energy-consumption"
        assert OwidSourceFinder.find_from_bullet_line(wikitext) == expected


class TestCheckUrl:
    """Tests for the check_url helper function."""

    def test_valid_ourworldindata_url(self):
        """Test valid ourworldindata.org URL."""
        result = OwidSourceFinder.check_url("https://ourworldindata.org/grapher/test")
        assert result is True

    def test_valid_www_ourworldindata_url(self):
        """Test valid www.ourworldindata.org URL."""
        result = OwidSourceFinder.check_url("https://www.ourworldindata.org/grapher/test")
        assert result is True

    def test_invalid_domain(self):
        """Test URL with invalid domain returns False (line 14)."""
        result = OwidSourceFinder.check_url("https://example.org/grapher/test")
        assert result is False

    def test_invalid_url_raises_value_error(self):
        """Test invalid URL that raises ValueError (lines 10-11)."""
        # URL with invalid format that causes urlparse to raise ValueError
        result = OwidSourceFinder.check_url("http://[invalid-url")
        assert result is False

    def test_case_insensitive_netloc(self):
        """Test that netloc matching is case insensitive."""
        result = OwidSourceFinder.check_url("https://OURWORLDINDATA.ORG/grapher/test")
        assert result is True


class TestFindTemplateSource3:
    """Tests for the find_template_source function (integration)."""

    def test_fallback_to_second_method(self):
        """Test that find_template_source falls back to find_from_bullet_line (line 80)."""
        # First method fails (no Source:), second method succeeds
        wikitext = "* https://ourworldindata.org/grapher/test"
        expected = "https://ourworldindata.org/grapher/test"
        result = OwidSourceFinder.find_template_source(wikitext)
        assert result == expected

    def test_both_methods_fail_returns_empty(self):
        """Test that find_template_source returns empty when both methods fail."""
        wikitext = "No valid URL here"
        result = OwidSourceFinder.find_template_source(wikitext)
        assert result == ""

    def test_first_method_succeeds(self):
        """Test that first method is tried first."""
        wikitext = "*'''Source''': https://ourworldindata.org/grapher/test"
        expected = "https://ourworldindata.org/grapher/test"
        result = OwidSourceFinder.find_template_source(wikitext)
        assert result == expected

    def test_check_url_false_in_find_template_source(self):
        """Test when check_url returns False in find_from_source_line (line 73)."""
        # Mock check_url to return False to test the guard clause
        wikitext = "*'''Source''': https://ourworldindata.org/grapher/test"
        with mock.patch("src.main_app.utils.new_wikitext.owid_source.OwidSourceFinder.check_url", return_value=False):
            result = OwidSourceFinder.find_from_source_line(wikitext)
            assert result == ""

    def test_check_url_false_in_find_template_source_2(self):
        """Test when check_url returns False in find_from_bullet_line (line 42)."""
        # Mock check_url to return False to test the guard clause
        wikitext = "* https://ourworldindata.org/grapher/test"
        with mock.patch("src.main_app.utils.new_wikitext.owid_source.OwidSourceFinder.check_url", return_value=False):
            result = OwidSourceFinder.find_from_bullet_line(wikitext)
            assert result == ""

    def test_urlparse_value_error_in_check_url(self):
        """Test that urlparse ValueError is handled in check_url (lines 10-11)."""
        with mock.patch("src.main_app.utils.new_wikitext.owid_source.urlparse", side_effect=ValueError("Invalid URL")):
            result = OwidSourceFinder.check_url("http://[invalid-url")
            assert result is False
