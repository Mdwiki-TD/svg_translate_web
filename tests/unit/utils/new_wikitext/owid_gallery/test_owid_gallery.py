from src.main_app.utils.new_wikitext.owid_gallery import SlidersGalleryReader

GALLERY = (
    "{{owidslidersrcs|id=gallery\n"
    "|gallery-World=\n"
    "File:a, World, 1950.svg!year=1950\n"
    "File:a, World, 1951.svg!year=1951\n"
    "}}"
)


class TestSlidersGalleryReaderMatch:
    """Tests for ``SlidersGalleryReader.match_newest_world_file``."""

    def test_picks_latest_date_including_full_dates(self):
        text = "File:a, World, 1952.svg!year=1952\nFile:a_b, World, Apr 15, 1953.svg!year=Apr 15, 1953"
        assert SlidersGalleryReader.match_newest_world_file(text) == "File:a b, World, Apr 15, 1953.svg"

    def test_ignores_invalid_lines(self):
        assert SlidersGalleryReader.match_newest_world_file("bad!year=1999\nno separator") == ""


class TestSlidersGalleryReaderFind:
    """Tests for the template based finders of ``SlidersGalleryReader``."""

    def test_find_newest_world_file(self):
        assert SlidersGalleryReader.find_newest_world_file(GALLERY) == "File:a, World, 1951.svg"

    def test_find_newest_world_file_without_prefix(self):
        assert SlidersGalleryReader.find_newest_world_file(GALLERY, remove_prefix=True) == "a, World, 1951.svg"

    def test_find_newest_year(self):
        assert SlidersGalleryReader.find_newest_year(GALLERY) == 1951

    def test_find_newest_year_without_template(self):
        assert SlidersGalleryReader.find_newest_year("plain") is None
