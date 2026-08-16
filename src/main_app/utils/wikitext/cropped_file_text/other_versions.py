""" """

from __future__ import annotations

import logging
from collections.abc import Callable

import wikitextparser as wtp

logger = logging.getLogger(__name__)

def get_args(template: wtp.Template, params: list[str]) -> wtp.Argument | None:
    for arg in params:
        if template.has_arg(arg) or template.has_arg(arg.lower()):
            arg_in = template.get_arg(arg) or template.get_arg(arg.lower())
            if arg_in:
                return arg_in
    return None

def add_other_versions_new(
    text: str,
    callback: Callable[[str]],
) -> str:
    """
    Add |other versions = <param_text> parameter to the {{Information}} template in wikitext.

    Args:
        text: The wikitext content to modify
        callback: A function that takes the wikitext content and returns the modified content

    Returns:
        The modified wikitext with the other versions parameter added

    TODO: if text include `{{Extracted from| Original.svg }}` and we need to add `{{Extracted from|1=Original.svg}}`
    """
    parsed = wtp.parse(text)
    args_names = ["other versions", "other_versions"]
    add_done = False
    for template in parsed.templates:
        if template.name.strip().lower() == "information":
            args_in = get_args(template, args_names)
            new_value = callback(args_in.value.strip() if args_in else "")
            formatted_new_value = f"{new_value.strip()}\n"
            if args_in:
                args_in.value = formatted_new_value
            else:
                template.set_arg("other versions", formatted_new_value)
            break

    if not add_done:
        return text

    return parsed.string


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

    TODO: if text include `{{Extracted from| Original.svg }}` and we need to add `{{Extracted from|1=Original.svg}}`
    """
    parsed = wtp.parse(text)
    args_names = ["other versions", "other_versions"]
    add_done = False
    for template in parsed.templates:
        if template.name.strip().lower() == "information":
            arg_found = False
            for arg in template.arguments:
                if arg.name.strip().lower() in args_names:

                    # NOTE: nothing to do here, to solve test_not_adding_duplicate_value
                    if param_text.strip() in arg.value.strip():
                        return text

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


__all__ = [
    "add_other_versions",
]
