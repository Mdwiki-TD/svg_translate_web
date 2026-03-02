"""

"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


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
    "update_template_page_file_reference",
]
