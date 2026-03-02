"""

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


__all__ = [
    "add_other_versions",
]
