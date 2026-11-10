"""
Helpers for file names and file references inside wikitext.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class FileReferenceUpdater:
    """Normalizes file names and rewrites file references."""

    def ensure_prefix(self, file_name) -> str:
        """Return ``file_name`` with a ``File:`` prefix; non-string or empty values are returned as is."""
        if not file_name or not isinstance(file_name, str):
            return file_name
        if not file_name.startswith("File:"):
            file_name = "File:" + file_name
        return file_name

    def update_template_page_file_reference(
        self,
        original_file: str,
        cropped_file: str,
        text: str,
    ) -> str:
        """
        Replace ``[[File:<original_file>|`` with ``[[File:<cropped_file>|`` everywhere in the text
        (including inside syntaxhighlight blocks).

        Both file names may be given with or without the ``File:`` prefix.
        """
        original_name = original_file.removeprefix("File:")
        cropped_name = cropped_file.removeprefix("File:")
        return text.replace(f"[[File:{original_name}|", f"[[File:{cropped_name}|")


__all__ = [
    "FileReferenceUpdater",
]
