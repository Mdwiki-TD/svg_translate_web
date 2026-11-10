""" """

from __future__ import annotations

from .before_methods import insert_before_methods
from .categories_utils import merge_categories, sort_categories
from .cropped_file_text import create_cropped_file_text
from .files_text import append_image_extracted_template, update_original_file_text
from .other_versions import OtherVersionsUpdater, add_other_versions_new
from .owid_sliders_rcs import (
    find_main_title,
    find_newest_world_file,
    find_newest_year,
)
from .temp_source import find_template_source
from .template_page import update_template_page_file_reference
from .temps_bot import count_svg_files, get_files_list_data, get_titles, get_titles_from_wikilinks


def ensure_file_prefix(file_name) -> str:
    if not file_name or not isinstance(file_name, str):
        return file_name
    if not file_name.startswith("File:"):
        file_name = "File:" + file_name
    return file_name


__all__ = [
    "OtherVersionsUpdater",
    "add_other_versions_new",
    "append_image_extracted_template",
    "count_svg_files",
    "create_cropped_file_text",
    "ensure_file_prefix",
    "find_main_title",
    "find_newest_world_file",
    "find_newest_year",
    "find_template_source",
    "get_files_list_data",
    "get_titles",
    "get_titles_from_wikilinks",
    "insert_before_methods",
    "merge_categories",
    "sort_categories",
    "update_original_file_text",
    "update_template_page_file_reference",
]
