"""
"""

from __future__ import annotations

from .before_mothods import insert_before_methods
from .other_versions import add_other_versions
from .template_page import update_template_page_file_reference
from .files_text import appendImageExtractedTemplate, update_original_file_text, create_cropped_file_text
from .temps_bot import get_titles, get_titles_from_wikilinks, get_files_list

__all__ = [
    "insert_before_methods",
    "add_other_versions",
    "update_original_file_text",
    "create_cropped_file_text",
    "update_template_page_file_reference",
    "appendImageExtractedTemplate",
    "update_original_file_text",
    "create_cropped_file_text",
    "get_titles",
    "get_titles_from_wikilinks",
    "get_files_list",
]
