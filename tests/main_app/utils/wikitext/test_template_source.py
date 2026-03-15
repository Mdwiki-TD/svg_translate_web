
from src.main_app.utils.wikitext.template_source import find_template_source


class TestFindTemplateSource:
    def test_find_template_source(self):
        wikitext = """
        *'''Source''': https://ourworldindata.org/grapher/share-electricity-renewables
        *'''Translate''': https://svgtranslate.toolforge.org/File:Share_electricity_renewables,_World,_1985.svg"""
        expected_source = "https://ourworldindata.org/grapher/share-electricity-renewables"
        result = find_template_source(wikitext)
        assert result == expected_source
