import pytest
import wikitextparser as wtp

from src.main_app.utils.new_wikitext.svg_files import SvgFilesCollector

GALLERY = (
    "{{owidslidersrcs|gallery-World=\n"
    "File:a, World, 1950.svg!year=1950\n"
    "File:a, World, 1951.svg!year=1951\n"
    "}}\n"
    "[[File:a, World, 1950.svg|thumb]] [[File:b, World, 1950 (cropped).svg|thumb]]"
)


def _wtp_works() -> bool:
    try:
        wtp.parse("a")
    except RuntimeError:
        return False
    return True


needs_wtp = pytest.mark.skipif(not _wtp_works(), reason="real wikitextparser is required")


class FakeTitleFinder:
    def find_main_title(self, text):
        return "FAKE TITLE"


class TestSvgFilesCollectorInjection:
    """Tests for the constructor of ``SvgFilesCollector``."""

    def test_uses_injected_title_finder(self):
        finder = FakeTitleFinder()
        assert SvgFilesCollector(title_finder=finder).title_finder is finder


@needs_wtp
class TestSvgFilesCollector:
    """Tests for ``SvgFilesCollector``."""

    def test_get_titles_reads_owidslidersrcs_files(self):
        assert sorted(SvgFilesCollector().get_titles(GALLERY)) == ["a, World, 1950.svg", "a, World, 1951.svg"]

    def test_get_titles_from_wikilinks_strips_prefix(self):
        titles = SvgFilesCollector().get_titles_from_wikilinks(GALLERY)
        assert titles == ["a, World, 1950.svg", "b, World, 1950 (cropped).svg"]

    def test_get_files_list_data_uses_injected_title_finder(self):
        data = SvgFilesCollector(title_finder=FakeTitleFinder()).get_files_list_data(GALLERY)
        assert data["main_title"] == "FAKE TITLE"
        assert len(data["titles"]) == 3

    def test_count_svg_files_counts_unique_files(self):
        assert SvgFilesCollector().count_svg_files(GALLERY) == 3
