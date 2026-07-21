"""Utility helpers for add_lang_categories_to_owid_pages worker."""

from __future__ import annotations

import re

from ....utils.file_langs import lang_code_category

# Matches the Translate/Translation link to extract the SVG file name.
# e.g. *'''Translate''': https://svgtranslate.toolforge.org/File:example.svg
RE_TRANSLATE = re.compile(
    r"\*\s*'''Translat\w+'''\s*:\s*https://svgtranslate\.toolforge\.org/File:([^ \n]+)",
    re.I,
)


def extract_svg_file_name(text: str) -> str | None:
    """Extract SVG file name from the Translate link in page wikitext.

    Args:
        text: Full wikitext of an OWID page.

    Returns:
        The SVG file name (without ``File:`` prefix), or ``None`` if not found.
    """
    match = RE_TRANSLATE.search(text)
    if match:
        return match.group(1).strip()
    return None


def build_category_names(lang_codes: list[str]) -> list[str]:
    """Convert language codes to ``Category:XXX-language SVG`` names.

    Args:
        lang_codes: List of Wikimedia language codes (e.g. ``["en", "ja", "ar"]``).

    Returns:
        List of ``Category:…`` strings (without ``[[…]]`` wrapper), suitable for
        passing directly to ``merge_categories_into_text``.
        Codes that ``lang_code_category()`` does not recognise are silently skipped.
    """
    categories: list[str] = []
    for code in lang_codes:
        cat = lang_code_category(code)
        if cat:
            categories.append(f"Category:{cat}")
    return categories


__all__ = [
    "extract_svg_file_name",
    "build_category_names",
]
