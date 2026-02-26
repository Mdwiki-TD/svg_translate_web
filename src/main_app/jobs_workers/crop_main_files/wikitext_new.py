"""
Module for handling upload of cropped SVG files to Wikimedia Commons.
"""

from __future__ import annotations

import logging
import re

import wikitextparser as wtp

logger = logging.getLogger(__name__)


def add_image_extracted_template(
    file_name: str,
    text: str,
) -> str:
    """
    """
    parsed = wtp.parse(text)
    args_names = [
        "other versions",
        "other_versions"
    ]
    param_text = f"{{{{Image extracted|1={file_name}}}}}"
    for template in parsed.templates:
        if template.name.strip().lower() == "information":
            arg_found = False
            for arg in template.arguments:
                if arg.name.strip().lower() in args_names:
                    new_value = arg.value.strip() + "\n" + param_text
                    arg.value = f"{new_value.strip()}\n"
                    arg_found = True
                    break
            if not arg_found:
                template.set_arg("other versions", f"{param_text}\n")

    # If no Information template found, return original text
    return parsed.string


def appendImageExtractedTemplate(
    cropped_file_name: str,
    text: str,
) -> str:
    """
    Update the original file's wikitext to include the cropped file information.
    # If the page already contains a {{Image extracted}} template, append the file to it

    """
    cropped_file_name = cropped_file_name.removeprefix("File:")
    template_name_regex = r"(extracted ?(images?|file|photo)?|image ?extracted|cropped version)"
    match = re.search(r"{{\s*" + template_name_regex + r"\s*(\s*|\|[^\}]+)}}", text, flags=re.IGNORECASE | re.MULTILINE)
    if not match:
        return add_image_extracted_template(cropped_file_name, text)

    start, length = match.start(), match.end() - match.start()
    tplText = text[start:start + length]

    # Find out how many existing arguments there are
    argNo = tplText.count('|') + 1

    # Append |$name before the }} of the template
    modified_text = text[:start + length - 2] + f"|{argNo}={cropped_file_name}" + text[start + length - 2:]

    return modified_text


__all__ = [
    "add_image_extracted_template",
    "appendImageExtractedTemplate",
]
