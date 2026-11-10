"""
Read the main title of OWID pages
(``{{SVGLanguages}}``, ``{{owidslidersrcs}}`` and svgtranslate links).
"""

from __future__ import annotations

import re
from urllib.parse import unquote, urlparse

import wikitextparser as wtp

# Valid SVG file name inside the ``gallery-World`` parameter
SVG_FILE_NAME_PATTERN = re.compile(r"^File:[\w\-,.()\s_]+\.svg$")


class MainTitleFinder:
    """Finds the main SVG title of a page using several strategies in order."""

    def match_main_title_from_url(self, text: str):
        """Match ``*'''Translate''': <svgtranslate url>`` lines that end the line."""
        pattern = r"^\*'''Translat(?:e|ion)''':\s+https?://svgtranslate\.toolforge\.org/(File:[\w\-,.()\s_]+\.svg)$"
        match = re.search(pattern, text, flags=re.M)
        return match.group(1) if match else None

    def match_main_title_from_url_new(self, text: str) -> str | None:
        """Return the SVG filename from the ``Translate`` line if present."""
        pattern = re.compile(
            r"^\*'''Translat(?:e|ion)''':\s+(?P<url>https?://svgtranslate\.toolforge\.org/[^\s]+)",
            flags=re.M | re.I,
        )
        match = pattern.search(text)
        if not match:
            return None

        # Wikitext links may wrap the URL with characters such as [] or quotes.
        url = match.group("url").rstrip("]')\">}")

        try:
            parsed = urlparse(url)
        except ValueError:
            return None

        if parsed.netloc.lower() != "svgtranslate.toolforge.org":
            return None

        path = unquote(parsed.path.lstrip("/"))
        if not path.lower().endswith(".svg"):
            return None

        return path

    def find_main_title_from_template(self, text: str) -> str | None:
        """Extract the main title from ``{{SVGLanguages|...}}``."""
        parsed = wtp.parse(text)

        main_title = None
        for tpl in parsed.templates:
            if tpl.name.strip().lower() == "svglanguages":
                if tpl.arguments:
                    main_title = tpl.arguments[0].value.strip()
                break
        if main_title:
            main_title = main_title.replace("_", " ").strip()

        return main_title

    def find_main_title_from_owidslidersrcs(self, text: str) -> str | None:
        """
        Return the first file of ``|gallery-World=`` in ``{{owidslidersrcs}}``.

        Example:
            {{owidslidersrcs|id=gallery
            |gallery-World=
            File:youth mortality rate, World, 1950.svg!year=1950
            }}
        Returns:
            "File:youth mortality rate, World, 1950.svg"
        """
        parsed = wtp.parse(text)

        main_title = None
        for tpl in parsed.templates:
            if tpl.name.strip().lower() == "owidslidersrcs":
                if tpl.arguments:
                    gallery = tpl.get_arg("gallery-World")
                    if gallery:
                        gallery = gallery.value.strip().splitlines()[0].split("!")[0].strip()
                        if SVG_FILE_NAME_PATTERN.match(gallery):
                            main_title = gallery.replace("_", " ").strip()
                break
        return main_title

    def find_main_title(self, text: str, remove_prefix: bool = False) -> str | None:
        """Find the main title, trying template, translate URL, then the gallery."""
        main_title = (
            self.find_main_title_from_template(text)
            or self.match_main_title_from_url_new(text)
            or self.match_main_title_from_url(text)
            or self.find_main_title_from_owidslidersrcs(text)
        )

        if main_title:
            main_title = main_title.replace("_", " ").strip()

        if main_title and remove_prefix:
            main_title = main_title.removeprefix("File:")
        return main_title


__all__ = [
    "MainTitleFinder",
]
