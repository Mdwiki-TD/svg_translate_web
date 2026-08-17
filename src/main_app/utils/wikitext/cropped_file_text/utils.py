"""
Utilities for manipulating wikitext files.
"""

from __future__ import annotations

import logging

from ..before_methods import insert_before_methods
from .other_versions import add_other_versions_new

logger = logging.getLogger(__name__)


def create_cropped_file_text(
    file_name: str,
    text: str,
) -> str:
    """
    Create wikitext for the cropped file based on the original file's wikitext.
    Args:
        file_name: The name of the original file
        text: The wikitext content of the original file
    Returns:
        The wikitext content for the cropped file
    """
    temp_name = "Extracted from"
    file_name = file_name.removeprefix("File:").replace("_", " ").strip()
    # add new argment like |other versions = {{Extracted from|1=Daily meat consumption per person, World, 2022.svg}} to template {{Information}} in the wikitext
    text_to_add = f"{{{{{temp_name}|1={file_name}}}}}"

    if not text or not text.strip():
        return text_to_add

    modified_text = add_other_versions_new(
        text=text,
        temp_name=temp_name,
        first_param_valve=file_name,
        main_template_name="Information",
        main_template_args=["other versions", "other_versions"],
    )

    if modified_text == text:
        modified_text = insert_before_methods(text, text_to_add)

    return modified_text


__all__ = [
    "create_cropped_file_text",
]
