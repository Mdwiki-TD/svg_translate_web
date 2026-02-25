"""
Module for handling upload of cropped SVG files to Wikimedia Commons.
"""

from __future__ import annotations

import logging
import wikitextparser as wtp
logger = logging.getLogger(__name__)


def add_other_versions(
    param_text: str,
    text: str,
) -> str:
    """
    Add |other versions = <param_text> parameter to the {{Information}} template in wikitext.

    Args:
        param_text: The text to add to the other versions parameter
        text: The wikitext content to modify

    Returns:
        The modified wikitext with the other versions parameter added
    """
    parsed = wtp.parse(text)

    for template in parsed.templates:
        if template.name.strip() == "Information":
            template.set_arg("other versions", param_text)
            return parsed.string

    # If no Information template found, return original text
    return text


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
    # add new argment like |other versions = {{Extracted from|1=Daily meat consumption per person, World, 2022.svg}} to template {{Information}} in the wikitext
    file_name = file_name.removeprefix("File:")
    other_versions_text = f"{{{{Extracted from|1={file_name}}}}}"
    modified_text = add_other_versions(other_versions_text, text)
    return modified_text


def update_original_file_text(
    cropped_file_name: str,
    text: str,
) -> str:
    """
    Update the original file's wikitext to include the cropped file information.
    """
    cropped_file_name = cropped_file_name.removeprefix("File:")
    other_versions_text = f"{{{{Image extracted|1={cropped_file_name}}}}}"
    modified_text = add_other_versions(other_versions_text, text)
    return modified_text
