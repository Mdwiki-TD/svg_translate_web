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

# Matches existing language SVG categories in wikitext.
# e.g. [[Category:English-language SVG]]
RE_LANG_CATEGORY = re.compile(r"\[\[Category:([^\]]*-language SVG)\]\]", re.I)


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


def build_category_lines(lang_codes: list[str]) -> list[str]:
    """Convert language codes to ``[[Category:XXX-language SVG]]`` lines.

    Args:
        lang_codes: List of Wikimedia language codes (e.g. ``["en", "ja", "ar"]``).

    Returns:
        List of category wikitext strings.  Codes that ``lang_code_category()``
        does not recognise are silently skipped.
    """
    categories: list[str] = []
    for code in lang_codes:
        cat = lang_code_category(code)
        if cat:
            categories.append(f"[[Category:{cat}]]")
    return categories


def get_existing_lang_categories(text: str) -> set[str]:
    """Parse page text to find existing ``*-language SVG`` categories.

    Args:
        text: Full wikitext of a page.

    Returns:
        Set of full category wikitext strings already present,
        e.g. ``{"[[Category:English-language SVG]]"}``.
    """
    return {f"[[Category:{name}]]" for name in RE_LANG_CATEGORY.findall(text)}


def add_categories_to_text(text: str, new_categories: list[str]) -> str:
    """Append category lines to the end of the page text.

    Args:
        text: Current page wikitext.
        new_categories: Category lines to append (e.g. ``["[[Category:Japanese-language SVG]]"]``).

    Returns:
        Updated wikitext with new categories appended.
    """
    if not new_categories:
        return text

    # Ensure there is a newline before the first appended category
    if text and not text.endswith("\n"):
        text += "\n"

    text += "\n".join(new_categories) + "\n"
    return text


__all__ = [
    "extract_svg_file_name",
    "build_category_lines",
    "get_existing_lang_categories",
    "add_categories_to_text",
]
