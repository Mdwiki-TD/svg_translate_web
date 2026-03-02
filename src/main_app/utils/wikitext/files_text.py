"""
Module for handling upload of cropped SVG files to Wikimedia Commons.
"""

from __future__ import annotations

import logging
import re
from .before_mothods import insert_before_methods
from .other_versions import add_other_versions

logger = logging.getLogger(__name__)


def appendImageExtractedTemplate(
    cropped_file_name: str,
    text: str,
) -> str:
    """
    Update the original file's wikitext to include the cropped file information.
    # If the page already contains a {{Image extracted}} template, append the file to it

    """
    if cropped_file_name.lower() in text.replace("_", " ").lower():
        return text
    cropped_file_name = cropped_file_name.removeprefix("File:")
    template_name_regex = r"(extracted ?(images?|file|photo)?|image ?extracted|cropped version)"
    match = re.search(r"{{\s*" + template_name_regex + r"\s*(\s*|\|[^\}]+)}}", text, flags=re.IGNORECASE | re.MULTILINE)
    if not match:
        return text

    start, length = match.start(), match.end() - match.start()
    tplText = text[start : start + length]

    # Find out how many existing arguments there are
    argNo = tplText.count("|") + 1

    # Append |$name before the }} of the template
    modified_text = text[: start + length - 2] + f"|{argNo}={cropped_file_name}" + text[start + length - 2 :]

    return modified_text


def update_original_file_text(
    cropped_file_name: str,
    text: str,
) -> str:
    """
    Update the original file's wikitext to include the cropped file information.
    """
    cropped_file_name = cropped_file_name.removeprefix("File:").replace("_", " ").strip()
    if cropped_file_name.lower() in text.replace("_", " ").lower():
        return text

    other_versions_text = f"{{{{Image extracted|1={cropped_file_name}}}}}"
    modified_text = appendImageExtractedTemplate(cropped_file_name, text)

    if modified_text == text:
        modified_text = add_other_versions(other_versions_text, text)

    if modified_text == text:
        modified_text = insert_before_methods(text, other_versions_text)

    return modified_text


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

    if not text:
        return other_versions_text

    modified_text = add_other_versions(other_versions_text, text)

    if modified_text == text:
        modified_text = insert_before_methods(text, other_versions_text)

    return modified_text


__all__ = [
    "appendImageExtractedTemplate",
    "update_original_file_text",
    "create_cropped_file_text",
]
