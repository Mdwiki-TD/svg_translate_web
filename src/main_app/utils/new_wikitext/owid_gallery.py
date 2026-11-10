"""
Read the the newest file/year of OWID pages
(``{{SVGLanguages}}``, ``{{owidslidersrcs}}`` and svgtranslate links).
"""

from __future__ import annotations

import re
from datetime import datetime

import wikitextparser as wtp

# Valid SVG file name inside the ``gallery-World`` parameter
SVG_FILE_NAME_PATTERN = re.compile(r"^File:[\w\-,.()\s_]+\.svg$")


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

    @staticmethod
    def match_newest_world_file(text: str) -> str:
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
                month = SlidersGalleryReader.MONTH_MAP.get(month_str.capitalize())
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

    @classmethod
    def find_newest_world_file(cls, text: str, remove_prefix: bool = False) -> str | None:
        """Return the newest file of the first ``{{owidslidersrcs}}`` template."""
        parsed = wtp.parse(text)

        newest_world_file = None
        for tpl in parsed.templates:
            if tpl.name.strip().lower() != "owidslidersrcs":
                continue

            if tpl.arguments:
                gallery = tpl.get_arg("gallery-World")
                if gallery:
                    matched = cls.match_newest_world_file(gallery.value.strip())
                    if matched:
                        newest_world_file = matched

            # Only the first owidslidersrcs template is used
            break

        if newest_world_file and remove_prefix:
            newest_world_file = newest_world_file.removeprefix("File:")

        return newest_world_file

    @staticmethod
    def find_newest_year(text: str) -> int | None:
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
    "SlidersGalleryReader",
]
