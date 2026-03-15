
from src.main_app.utils.wikitext.template_source import find_template_source


class TestFindTemplateSource:
    def test_basic(self):
        wikitext = """
        *'''Source''': https://ourworldindata.org/grapher/share-electricity-renewables
        *'''Translate''': https://svgtranslate.toolforge.org/File:Share_electricity_renewables,_World,_1985.svg
        """
        expected = "https://ourworldindata.org/grapher/share-electricity-renewables"
        assert find_template_source(wikitext) == expected

    def test_with_www(self):
        wikitext = "*'''Source''': https://www.ourworldindata.org/grapher/co2-emissions"
        expected = "https://www.ourworldindata.org/grapher/co2-emissions"
        assert find_template_source(wikitext) == expected

    def test_http_scheme(self):
        wikitext = "*'''Source''': http://ourworldindata.org/grapher/co2-emissions"
        expected = "http://ourworldindata.org/grapher/co2-emissions"
        assert find_template_source(wikitext) == expected

    def test_trailing_characters(self):
        wikitext = "*'''Source''': https://ourworldindata.org/grapher/life-expectancy]]"
        expected = "https://ourworldindata.org/grapher/life-expectancy"
        assert find_template_source(wikitext) == expected

    def test_extra_spaces(self):
        wikitext = "*'''Source''':     https://ourworldindata.org/grapher/gdp-per-capita"
        expected = "https://ourworldindata.org/grapher/gdp-per-capita"
        assert find_template_source(wikitext) == expected

    def test_case_insensitive_source(self):
        wikitext = "*'''SOURCE''': https://ourworldindata.org/grapher/energy-consumption"
        expected = "https://ourworldindata.org/grapher/energy-consumption"
        assert find_template_source(wikitext) == expected

    def test_multiple_lines(self):
        wikitext = """
        some text
        *'''Source''': https://ourworldindata.org/grapher/child-mortality
        more text
        """
        expected = "https://ourworldindata.org/grapher/child-mortality"
        assert find_template_source(wikitext) == expected

    def test_invalid_domain(self):
        wikitext = "*'''Source''': https://example.org/data"
        assert find_template_source(wikitext) == ""

    def test_missing_source(self):
        wikitext = "*'''Translate''': https://svgtranslate.toolforge.org/File:test.svg"
        assert find_template_source(wikitext) == ""

    def test_with_wikilink_brackets(self):
        wikitext = "*'''Source''': [https://ourworldindata.org/grapher/population-growth]"
        assert find_template_source(wikitext) == ""
