import pytest
import wikitextparser as wtp

from src.main_app.utils.new_wikitext.owid_gallery import MainTitleFinder, SlidersGalleryReader

GALLERY = (
    "{{owidslidersrcs|id=gallery\n"
    "|gallery-World=\n"
    "File:a, World, 1950.svg!year=1950\n"
    "File:a, World, 1951.svg!year=1951\n"
    "}}"
)


def _wtp_works() -> bool:
    try:
        wtp.parse("a")
    except RuntimeError:
        return False
    return True


needs_wtp = pytest.mark.skipif(not _wtp_works(), reason="real wikitextparser is required")


class TestMainTitleFinderUrl:
    """Tests for the svgtranslate URL matchers of ``MainTitleFinder``."""

    def test_new_matcher_returns_decoded_file_path(self):
        text = "*'''Translate''': https://svgtranslate.toolforge.org/File:Foo_bar%2C_World.svg"
        assert MainTitleFinder().match_main_title_from_url_new(text) == "File:Foo_bar,_World.svg"

    def test_new_matcher_rejects_non_svg(self):
        text = "*'''Translate''': https://svgtranslate.toolforge.org/File:a.png"
        assert MainTitleFinder().match_main_title_from_url_new(text) is None

    def test_old_matcher_requires_full_line(self):
        text = "*'''Translation''': https://svgtranslate.toolforge.org/File:A_b,_World.svg"
        assert MainTitleFinder().match_main_title_from_url(text) == "File:A_b,_World.svg"


@needs_wtp
class TestMainTitleFinderFind:
    """Tests for ``MainTitleFinder.find_main_title``."""

    def test_reads_svglanguages_template(self):
        assert MainTitleFinder().find_main_title("{{SVGLanguages|my_file,World,1990.svg}}") == "my file,World,1990.svg"

    def test_reads_first_gallery_file(self):
        assert MainTitleFinder().find_main_title(GALLERY) == "File:a, World, 1950.svg"

    def test_remove_prefix(self):
        assert MainTitleFinder().find_main_title(GALLERY, remove_prefix=True) == "a, World, 1950.svg"


class TestSlidersGalleryReaderMatch:
    """Tests for ``SlidersGalleryReader.match_newest_world_file``."""

    def test_picks_latest_date_including_full_dates(self):
        text = "File:a, World, 1952.svg!year=1952\nFile:a_b, World, Apr 15, 1953.svg!year=Apr 15, 1953"
        assert SlidersGalleryReader().match_newest_world_file(text) == "File:a b, World, Apr 15, 1953.svg"

    def test_ignores_invalid_lines(self):
        assert SlidersGalleryReader().match_newest_world_file("bad!year=1999\nno separator") == ""


@needs_wtp
class TestSlidersGalleryReaderFind:
    """Tests for the template based finders of ``SlidersGalleryReader``."""

    def test_find_newest_world_file(self):
        assert SlidersGalleryReader().find_newest_world_file(GALLERY) == "File:a, World, 1951.svg"

    def test_find_newest_world_file_without_prefix(self):
        assert SlidersGalleryReader().find_newest_world_file(GALLERY, remove_prefix=True) == "a, World, 1951.svg"

    def test_find_newest_year(self):
        assert SlidersGalleryReader().find_newest_year(GALLERY) == 1951

    def test_find_newest_year_without_template(self):
        assert SlidersGalleryReader().find_newest_year("plain") is None
