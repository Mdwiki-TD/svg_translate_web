
from src.main_app.utils.wikitext.template_source import _find_template_source, _find_template_source_2


class TestFindTemplateSource:
    def test_basic(self):
        wikitext = """
        *'''Source''': https://ourworldindata.org/grapher/share-electricity-renewables
        *'''Translate''': https://svgtranslate.toolforge.org/File:Share_electricity_renewables,_World,_1985.svg
        """
        expected = "https://ourworldindata.org/grapher/share-electricity-renewables"
        assert _find_template_source(wikitext) == expected

    def test_with_www(self):
        wikitext = "*'''Source''': https://www.ourworldindata.org/grapher/co2-emissions"
        expected = "https://www.ourworldindata.org/grapher/co2-emissions"
        assert _find_template_source(wikitext) == expected

    def test_http_scheme(self):
        wikitext = "*'''Source''': http://ourworldindata.org/grapher/co2-emissions"
        expected = "http://ourworldindata.org/grapher/co2-emissions"
        assert _find_template_source(wikitext) == expected

    def test_trailing_characters(self):
        wikitext = "*'''Source''': https://ourworldindata.org/grapher/life-expectancy]]"
        expected = "https://ourworldindata.org/grapher/life-expectancy"
        assert _find_template_source(wikitext) == expected

    def test_extra_spaces(self):
        wikitext = "*'''Source''':     https://ourworldindata.org/grapher/gdp-per-capita"
        expected = "https://ourworldindata.org/grapher/gdp-per-capita"
        assert _find_template_source(wikitext) == expected

    def test_case_insensitive_source(self):
        wikitext = "*'''SOURCE''': https://ourworldindata.org/grapher/energy-consumption"
        expected = "https://ourworldindata.org/grapher/energy-consumption"
        assert _find_template_source(wikitext) == expected

    def test_multiple_lines(self):
        wikitext = """
        some text
        *'''Source''': https://ourworldindata.org/grapher/child-mortality
        more text
        """
        expected = "https://ourworldindata.org/grapher/child-mortality"
        assert _find_template_source(wikitext) == expected

    def test_invalid_domain(self):
        wikitext = "*'''Source''': https://example.org/data"
        assert _find_template_source(wikitext) == ""

    def test_missing_source(self):
        wikitext = "*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg"
        assert _find_template_source(wikitext) == ""

    def test_with_wikilink_brackets(self):
        wikitext = "*'''Source''': [https://ourworldindata.org/grapher/population-growth]"
        assert _find_template_source(wikitext) == ""


class TestFindTemplateSource2:
    def test_basic_http(self):
        wikitext = """
        * http://ourworldindata.org/grapher/share-electricity-renewables
        """
        expected = "http://ourworldindata.org/grapher/share-electricity-renewables"
        assert _find_template_source_2(wikitext) == expected

    def test_https(self):
        wikitext = "* https://ourworldindata.org/grapher/co2-emissions"
        expected = "https://ourworldindata.org/grapher/co2-emissions"
        assert _find_template_source_2(wikitext) == expected

    def test_with_www(self):
        wikitext = "* https://www.ourworldindata.org/grapher/population"
        expected = "https://www.ourworldindata.org/grapher/population"
        assert _find_template_source_2(wikitext) == expected

    def test_spaces_before_star(self):
        wikitext = "      * https://ourworldindata.org/grapher/gdp-per-capita"
        expected = "https://ourworldindata.org/grapher/gdp-per-capita"
        assert _find_template_source_2(wikitext) == expected

    def test_spaces_after_star(self):
        wikitext = "*     https://ourworldindata.org/grapher/life-expectancy"
        expected = "https://ourworldindata.org/grapher/life-expectancy"
        assert _find_template_source_2(wikitext) == expected

    def test_wikilink_brackets(self):
        wikitext = "* [https://ourworldindata.org/grapher/child-mortality]"
        assert _find_template_source_2(wikitext) == ""

    def test_trailing_characters(self):
        wikitext = "* https://ourworldindata.org/grapher/fertility-rate]]"
        expected = "https://ourworldindata.org/grapher/fertility-rate"
        assert _find_template_source_2(wikitext) == expected

    def test_invalid_domain(self):
        wikitext = "* https://example.org/data"
        assert _find_template_source_2(wikitext) == ""

    def test_no_url(self):
        wikitext = "* some text without a url"
        assert _find_template_source_2(wikitext) == ""

    def test_url_not_first_in_line(self):
        wikitext = "* source https://ourworldindata.org/grapher/test"
        assert _find_template_source_2(wikitext) == ""

    def test_multiple_lines(self):
        wikitext = """
        text
        * https://ourworldindata.org/grapher/energy-consumption
        another line
        """
        expected = "https://ourworldindata.org/grapher/energy-consumption"
        assert _find_template_source_2(wikitext) == expected
