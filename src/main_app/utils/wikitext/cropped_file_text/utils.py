"""
Utilities for manipulating wikitext files.
"""

from __future__ import annotations

import logging

import wikitextparser as wtp

from ..before_methods import insert_before_methods
from .other_versions import add_other_versions_new

logger = logging.getLogger(__name__)


def update_information_author(text: str, author_citation: str | None) -> str:
    """Replace the Author value in the first ``{{Information}}`` template.

    Args:
        text: The original file-description wikitext.
        author_citation: The complete attribution to set. Empty values leave the text unchanged.

    Returns:
        The modified wikitext, or the original text if no Information template exists.
    """
    if not author_citation:
        return text

    parsed = wtp.parse(text)
    for template in parsed.templates:
        if template.name.strip().lower() != "information":
            continue

        for argument in template.arguments:
            if argument.name.strip().lower() == "author":

                if argument.value.strip().lower() == "our world in data":
                    argument.value = f" {author_citation}\n"
                    return parsed.string

                if argument.value.strip() == author_citation:
                    return text

                argument.value = f" {author_citation}\n"
                return parsed.string

        template.set_arg("author", f" {author_citation}\n")
        return parsed.string

    return text


def create_cropped_file_text(
    file_name: str,
    text: str,
    author_citation: str | None = None,
) -> str:
    """
    Create cropped-file wikitext and optionally enrich its Author attribution.

    Args:
        file_name: The name of the original file.
        text: The wikitext content of the original file.
        author_citation: A canonical upstream-source citation from OWID metadata.

    Returns:
        The wikitext content for the cropped file.
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

    if author_citation:
        modified_text = update_information_author(modified_text, author_citation)
    return modified_text


__all__ = [
    "create_cropped_file_text",
    "update_information_author",
]
