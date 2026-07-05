""" """

import re
from datetime import datetime

import wikitextparser as wtp


def match_newest_world_file(text: str) -> str:
    """
    Example:
        ==Data==
        {{owidslidersrcs|id=gallery|widths=240|heights=240
        |gallery-World=
        File:youth mortality rate, World, 1950.svg!year=1950
        File:youth mortality rate, World, 1951.svg!year=1951
        File:youth mortality rate, World, 1952.svg!year=1952
        File:youth mortality rate, World, Apr 15, 1953.svg!year=Apr 15, 1953
        }}
    Returns:
        "File:youth mortality rate, World, Apr 15, 1953.svg"
    """
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
        m = re.match(r"^File:[\w\-,.()\s_]+\.svg$", filename)
        if not m:
            continue

        # Try full date: "year=Apr 15, 1940"
        date_match = re.match(r"year\s*=\s*([A-Za-z]{3})\s+(\d{1,2}),\s*(\d{4})\s*$", year_part)
        if date_match:
            month_str, day_str, year_str = date_match.groups()
            month = MONTH_MAP.get(month_str.capitalize())
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


def find_newest_world_file(text: str, remove_prefix: bool = False) -> str | None:
    """ """
    # Parse the text using wikitextparser
    parsed = wtp.parse(text)

    # --- 1. Extract newest_world_file from {{owidslidersrcs|gallery-World=...}}
    newest_world_file = None
    for tpl in parsed.templates:
        if tpl.name.strip().lower() != "owidslidersrcs":
            continue

        if tpl.arguments:
            gallery = tpl.get_arg("gallery-World")
            if gallery:
                matched = match_newest_world_file(gallery.value.strip())
                if matched:
                    newest_world_file = matched

        # break when match owidslidersrcs template
        break

    if newest_world_file and remove_prefix:
        newest_world_file = newest_world_file.removeprefix("File:")

    return newest_world_file


def find_newest_year(text: str) -> int | None:
    """ """
    # Parse the text using wikitextparser
    parsed = wtp.parse(text)

    # --- 1. Extract last_world_year from {{owidslidersrcs|gallery-World=...}}
    last_world_year = None
    for tpl in parsed.templates:
        if tpl.name.strip().lower() != "owidslidersrcs":
            continue
        tpl_text = tpl.string
        # match all `!year=2009` in tpl_text then select the biggest year
        matches = re.findall(r"!\s*year\s*=\s*(\d{4})", tpl_text)
        if matches:
            last_world_year = max(matches)
        # break when match owidslidersrcs template
        break

    if isinstance(last_world_year, str):
        last_world_year = int(last_world_year)

    return last_world_year


__all__ = [
    "match_newest_world_file",
    "find_newest_world_file",
    "find_newest_year",
]
