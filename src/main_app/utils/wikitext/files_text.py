"""
Utilities for manipulating wikitext files.
"""

from __future__ import annotations

import logging
import re

from .before_methods import insert_before_methods
from .cropped_file_text import add_other_versions_new

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
    match = re.search(r"{{\s*" + template_name_regex + r"\s*(\s*|\|[^\}]+)}}", text, flags=re.I | re.M)
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
    file_name: str,
    text: str,
) -> str:
    """
    Update the original file's wikitext to include the cropped file information.
    """
    temp_name = "Image extracted"
    file_name = file_name.removeprefix("File:").replace("_", " ").strip()
    if file_name.lower() in text.replace("_", " ").lower():
        return text

    text_to_add = f"{{{{{temp_name}|1={file_name}}}}}"

    modified_text = append_image_extracted_template(file_name, text)

    if modified_text == text:
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
    "append_image_extracted_template",
    "update_original_file_text",
]
