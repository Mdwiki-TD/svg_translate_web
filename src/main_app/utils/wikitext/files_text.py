"""
Utilities for manipulating wikitext files.
"""

from __future__ import annotations

import logging
import re

import wikitextparser as wtp

from .before_methods import insert_before_methods
from .other_versions import add_other_versions

logger = logging.getLogger(__name__)


def append_image_extracted_template(
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
    modified_text = append_image_extracted_template(cropped_file_name, text)

    if modified_text == text:
        modified_text = add_other_versions(other_versions_text, text)

    if modified_text == text:
        modified_text = insert_before_methods(text, other_versions_text)

    return modified_text


def update_information_author(text: str, author: str | None) -> str:
    """Replace the Author value in the first ``{{Information}}`` template.

    Args:
        text: The original file-description wikitext.
        author: The complete attribution to set. Empty values leave the text unchanged.

    Returns:
        The modified wikitext, or the original text if no Information template exists.
    """
    if not author:
        return text

    parsed = wtp.parse(text)
    for template in parsed.templates:
        if template.name.strip().lower() != "information":
            continue

        for argument in template.arguments:
            if argument.name.strip().lower() == "author":
                if argument.value.strip() == author:
                    return text
                argument.value = f" {author}\n"
                return parsed.string

        template.set_arg("author", f" {author}\n")
        return parsed.string

    return text


def create_cropped_file_text(
    file_name: str,
    text: str,
    author_citation: str | None = None,
) -> str:
    """Create cropped-file wikitext and optionally enrich its Author attribution.

    Args:
        file_name: The name of the original file.
        text: The wikitext content of the original file.
        author_citation: A canonical upstream-source citation from OWID metadata.

    Returns:
        The wikitext content for the cropped file.
    """
    # Add an ``other versions`` parameter pointing to the original file.
    file_name = file_name.removeprefix("File:")
    other_versions_text = f"{{{{Extracted from|1={file_name}}}}}"

    if not text:
        return other_versions_text

    modified_text = update_information_author(text, author_citation)
    if other_versions_text in modified_text:
        return modified_text

    text_with_other_versions = add_other_versions(other_versions_text, modified_text)
    if text_with_other_versions == modified_text:
        text_with_other_versions = insert_before_methods(modified_text, other_versions_text)

    return text_with_other_versions


__all__ = [
    "append_image_extracted_template",
    "create_cropped_file_text",
    "update_information_author",
    "update_original_file_text",
]
