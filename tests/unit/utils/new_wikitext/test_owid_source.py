from src.main_app.utils.new_wikitext.owid_source import OwidSourceFinder

SOURCE_LINE = "*'''Source''': https://ourworldindata.org/grapher/foo-bar]\n"


class TestOwidSourceFinderCheckUrl:
    """Tests for ``OwidSourceFinder.check_url``."""

    def test_accepts_owid_hosts(self):
        assert OwidSourceFinder().check_url("https://www.ourworldindata.org/x") is True

    def test_rejects_other_hosts(self):
        assert OwidSourceFinder().check_url("https://example.org/x") is False

    def test_rejects_invalid_url(self):
        assert OwidSourceFinder().check_url("http://[bad") is False


class TestOwidSourceFinderFind:
    """Tests for ``OwidSourceFinder.find_template_source``."""

    def test_finds_source_line_and_strips_trailing_chars(self):
        assert OwidSourceFinder().find_template_source(SOURCE_LINE) == "https://ourworldindata.org/grapher/foo-bar"

    def test_finds_bullet_line(self):
        text = "* https://ourworldindata.org/grapher/baz\n"
        assert OwidSourceFinder().find_template_source(text) == "https://ourworldindata.org/grapher/baz"

    def test_requires_grapher_by_default(self):
        text = "* https://ourworldindata.org/explorers/x\n"
        finder = OwidSourceFinder()
        assert finder.find_template_source(text) == ""
        assert finder.find_template_source(text, check_grapher=False) == "https://ourworldindata.org/explorers/x"

    def test_returns_empty_when_missing(self):
        assert OwidSourceFinder().find_template_source("nothing") == ""
