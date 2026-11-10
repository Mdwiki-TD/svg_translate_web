"""
Read the main title and the newest file/year of OWID pages
(``{{SVGLanguages}}``, ``{{owidslidersrcs}}`` and svgtranslate links).
"""

from __future__ import annotations

import re
from datetime import datetime
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


class SlidersGalleryReader:
    """Reads the newest world file and the newest year of ``{{owidslidersrcs}}``."""

    MONTH_MAP = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }

    def match_newest_world_file(self, text: str) -> str:
        """
        Return the file with the latest date in a ``gallery-World`` value.

        Example:
            File:youth mortality rate, World, 1952.svg!year=1952
            File:youth mortality rate, World, Apr 15, 1953.svg!year=Apr 15, 1953
        Returns:
            "File:youth mortality rate, World, Apr 15, 1953.svg"
        """
        lines = text.strip().splitlines()
        latest_date = None
        newest_world_file = ""

        for line in lines:
            parts = line.split("!")
            if len(parts) < 2:
                continue

            filename = parts[0].strip()
            year_part = parts[1].strip()

            # Validate filename format
            if not SVG_FILE_NAME_PATTERN.match(filename):
                continue

            # Try full date: "year=Apr 15, 1940"
            date_match = re.match(r"year\s*=\s*([A-Za-z]{3})\s+(\d{1,2}),\s*(\d{4})\s*$", year_part)
            if date_match:
                month_str, day_str, year_str = date_match.groups()
                month = self.MONTH_MAP.get(month_str.capitalize())
                if month is None:
                    continue
                date = datetime(int(year_str), month, int(day_str))
            else:
                # Fallback: "year=1953"
                simple_match = re.match(r"year\s*=\s*(\d{4})\s*$", year_part)
                if not simple_match:
                    continue
                date = datetime(int(simple_match.group(1)), 1, 1)

            if latest_date is None or date > latest_date:
                latest_date = date
                newest_world_file = filename.replace("_", " ").strip()

        return newest_world_file

    def find_newest_world_file(self, text: str, remove_prefix: bool = False) -> str | None:
        """Return the newest file of the first ``{{owidslidersrcs}}`` template."""
        parsed = wtp.parse(text)

        newest_world_file = None
        for tpl in parsed.templates:
            if tpl.name.strip().lower() != "owidslidersrcs":
                continue

            if tpl.arguments:
                gallery = tpl.get_arg("gallery-World")
                if gallery:
                    matched = self.match_newest_world_file(gallery.value.strip())
                    if matched:
                        newest_world_file = matched

            # Only the first owidslidersrcs template is used
            break

        if newest_world_file and remove_prefix:
            newest_world_file = newest_world_file.removeprefix("File:")

        return newest_world_file

    def find_newest_year(self, text: str) -> int | None:
        """Return the biggest ``!year=YYYY`` of the first ``{{owidslidersrcs}}`` template."""
        parsed = wtp.parse(text)

        last_world_year = None
        for tpl in parsed.templates:
            if tpl.name.strip().lower() != "owidslidersrcs":
                continue
            matches = re.findall(r"!\s*year\s*=\s*(\d{4})", tpl.string)
            if matches:
                last_world_year = max(matches)
            # Only the first owidslidersrcs template is used
            break

        if isinstance(last_world_year, str):
            last_world_year = int(last_world_year)

        return last_world_year


__all__ = [
    "MainTitleFinder",
    "SlidersGalleryReader",
]
