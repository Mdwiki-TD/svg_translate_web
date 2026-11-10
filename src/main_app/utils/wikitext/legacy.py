"""
Backward-compatible function API.

Every function here keeps its original name, signature and defaults and only
delegates to the class-based implementation. No business logic lives here and
no deprecation warnings are emitted.
"""

from __future__ import annotations

from ..new_wikitext.categories import CategoryExtractor, CategoryLink, CategoryMerger
from ..new_wikitext.file_references import FileReferenceUpdater
from ..new_wikitext.file_text import CroppedFileTextBuilder, OriginalFileTextUpdater
from ..new_wikitext.insertion import BeforeMarkerInserter
from ..new_wikitext.main_title_finder import MainTitleFinder
from ..new_wikitext.owid_gallery import SlidersGalleryReader
from ..new_wikitext.owid_source import OwidSourceFinder
from ..new_wikitext.svg_files import SvgFilesCollector

# ---- before_methods ----


def insert_before_methods(text: str, other_versions_text: str) -> str:
    return BeforeMarkerInserter.insert_before_methods(text, other_versions_text)


# ---- categories_utils ----


def capitalize_category(str_category) -> str:
    """Capitalize the first letter of each part in a category string separated by a colon."""
    return CategoryExtractor().capitalize_category(str_category)


def create_category_link_from_str(str_link: str) -> CategoryLink:
    """Create a CategoryLink object from a string representation of a wiki link."""
    return CategoryExtractor().create_category_link_from_str(str_link)


def extract_categories(wikitext: str) -> list[CategoryLink]:
    """Extract category WikiLinks from the given wikitext."""
    return CategoryExtractor().extract_categories(wikitext)


def find_missing_categories(
    target_categories: list[CategoryLink],
    base_categories: list[CategoryLink],
) -> list[CategoryLink]:
    """Identify categories in 'base_categories' that are missing from 'target_categories'."""
    return CategoryMerger().find_missing_categories(target_categories, base_categories)


def merge_categories(old_text: str, new_text: str) -> str:
    """Append categories found in old_text to new_text if they are not already present."""
    return CategoryMerger().merge_categories(old_text, new_text)


def sort_categories(wikitext: str) -> str:
    """Move all categories to the end of the text, sorted."""
    return CategoryMerger().sort_categories(wikitext)


def get_missing_categories_list(cats_list: list[str], text: str) -> list[str]:
    return CategoryMerger().get_missing_categories_list(cats_list, text)


def merge_categories_into_text(cats_list: list[str], text: str) -> str:
    """Append the categories of cats_list that are missing from text."""
    return CategoryMerger().merge_categories_into_text(cats_list, text)


# ---- files_text ----


def append_image_extracted_template(
    cropped_file_name: str,
    text: str,
) -> str:
    """Append the cropped file to an existing extracted-image template."""
    return OriginalFileTextUpdater.append_image_extracted_template(cropped_file_name, text)


def update_original_file_text(
    file_name: str,
    text: str,
) -> str:
    """Update the original file's wikitext to include the cropped file information."""
    return OriginalFileTextUpdater().update_original_file_text(file_name, text)


# ---- cropped_file_text.utils ----


def create_cropped_file_text(
    file_name: str,
    text: str,
    author_citation: str | None = None,
) -> str:
    """Create cropped-file wikitext and optionally enrich its Author attribution."""
    return CroppedFileTextBuilder().create_cropped_file_text(file_name, text, author_citation)


# ---- template_page ----


def update_template_page_file_reference(
    original_file: str,
    cropped_file: str,
    text: str,
) -> str:
    """Replace the file reference in a template page's wikitext."""
    return FileReferenceUpdater.update_template_page_file_reference(original_file, cropped_file, text)


# ---- temp_source ----


def check_url(url: str) -> bool:
    return OwidSourceFinder().check_url(url)


def _find_template_source_2(wikitext: str) -> str:
    return OwidSourceFinder().find_from_bullet_line(wikitext)


def _find_template_source(wikitext: str) -> str:
    return OwidSourceFinder().find_from_source_line(wikitext)


def find_template_source(wikitext: str, check_grapher: bool = True) -> str:
    return OwidSourceFinder().find_template_source(wikitext, check_grapher)


# ---- owid_gallery.main_file ----


def match_main_title_from_url(text: str):
    return MainTitleFinder().match_main_title_from_url(text)


def match_main_title_from_url_new(text: str) -> str | None:
    """Return the SVG filename from the ``Translate`` line if present."""
    return MainTitleFinder().match_main_title_from_url_new(text)


def find_main_title_from_template(text: str) -> str | None:
    return MainTitleFinder().find_main_title_from_template(text)


def find_main_title_from_owidslidersrcs(text: str) -> str | None:
    return MainTitleFinder().find_main_title_from_owidslidersrcs(text)


def find_main_title(text: str, remove_prefix: bool = False) -> str | None:
    return MainTitleFinder().find_main_title(text, remove_prefix)


# ---- owid_gallery.owidslidersrcs_utils ----


def match_newest_world_file(text: str) -> str:
    return SlidersGalleryReader.match_newest_world_file(text)


def find_newest_world_file(text: str, remove_prefix: bool = False) -> str | None:
    return SlidersGalleryReader.find_newest_world_file(text, remove_prefix)


def find_newest_year(text: str) -> int | None:
    return SlidersGalleryReader.find_newest_year(text)


# ---- temps_bot ----


def get_titles_from_wikilinks(text: str) -> list:
    return SvgFilesCollector().get_titles_from_wikilinks(text)


def get_titles(text: str, filter_duplicates: bool = True) -> list[str]:
    return SvgFilesCollector().get_titles(text, filter_duplicates)


def get_files_list_data(text: str, filter_duplicates: bool = True) -> dict:
    return SvgFilesCollector().get_files_list_data(text, filter_duplicates)


def count_svg_files(text: str) -> int:
    return SvgFilesCollector().count_svg_files(text)
