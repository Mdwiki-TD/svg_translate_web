"""
Module for handling upload of cropped SVG files to Wikimedia Commons.
"""

from __future__ import annotations

import logging
import re

import wikitextparser as wtp

logger = logging.getLogger(__name__)


def addBefore(text: str, newText: str, searchText: str) -> str:
    res = re.search(searchText, text, flags=re.IGNORECASE | re.MULTILINE)
    if res:
        start = res.start()
        text = text[:start].rstrip() + "\n" + newText + "\n\n" + text[start:].lstrip()
    return text


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
    args_names = ["other versions", "other_versions"]
    add_done = False
    for template in parsed.templates:
        if template.name.strip().lower() == "information":
            arg_found = False
            for arg in template.arguments:
                if arg.name.strip().lower() in args_names:
                    new_value = arg.value.strip() + "\n" + param_text
                    arg.value = f"{new_value.strip()}\n"
                    arg_found = True
                    add_done = True
                    break
            if not arg_found:
                template.set_arg("other versions", f"{param_text}\n")
                add_done = True
                break
            break

    if not add_done:
        return text

    return parsed.string


def insert_before_methods(text, other_versions_text):
    # Try to add before the license header
    modified_text = addBefore(text, other_versions_text, r"==\s*\{\{\s*int:license-header\s*\}\}\s*==")

    if modified_text == text:
        # Try to add before the first category
        modified_text = addBefore(text, other_versions_text, r"\[\[\s*category:")
    return modified_text


def appendImageExtractedTemplate(
    cropped_file_name: str,
    text: str,
) -> str:
    """
    Update the original file's wikitext to include the cropped file information.
    # If the page already contains a {{Image extracted}} template, append the file to it

    """
    if cropped_file_name.lower() in text.lower():
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
    if cropped_file_name.lower() in text.lower():
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


def update_template_page_file_reference(
    original_file: str,
    cropped_file: str,
    text: str,
) -> str:
    """
    Replace the file reference in a template page's wikitext.

    Replaces [[File:<original_file>...]] with [[File:<cropped_file>...]]
    everywhere in the template page wikitext (including inside syntaxhighlight blocks).

    Args:
        original_file: The original world file name (with or without "File:" prefix)
        cropped_file: The cropped file name (with or without "File:" prefix)
        text: The template page wikitext to modify

    Returns:
        The modified wikitext with file references replaced
    """
    original_name = original_file.removeprefix("File:")
    cropped_name = cropped_file.removeprefix("File:")
    return text.replace(f"[[File:{original_name}|", f"[[File:{cropped_name}|")


__all__ = [
    "update_original_file_text",
    "create_cropped_file_text",
    "update_template_page_file_reference",
]
