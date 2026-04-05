""" """

import re
from datetime import datetime

import wikitextparser as wtp


def match_last_world_file_with_full_date(text) -> str:
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
    last_world_file = ""

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
            last_world_file = filename.replace("_", " ").strip()

    return last_world_file


def match_last_world_file(text) -> str:
    """
    Example:
        ==Data==
        {{owidslidersrcs|id=gallery|widths=240|heights=240
        |gallery-World=
        File:youth mortality rate, World, 1950.svg!year=1950
        File:youth mortality rate, World, 1951.svg!year=1951
        File:youth mortality rate, World, 1952.svg!year=1952
        File:youth mortality rate, World, 1953.svg!year=1953
        }}
    Returns:
        "File:youth mortality rate, World, 1953.svg"
    """

    lines = text.splitlines()
    max_year = -1
    last_world_file = ""

    for line in lines:
        # Extract filename and year part
        parts = line.split("!")
        if len(parts) < 2:
            continue

        filename = parts[0].strip()
        year_part = parts[1].strip()

        # Validate filename format
        m = re.match(r"^File:[\w\-,.()\s_]+\.svg$", filename)
        if not m:
            continue

        # Extract year from "year=1953" format
        year_match = re.match(r"year\s*=\s*(\d{4})", year_part)
        if not year_match:
            continue

        year = int(year_match.group(1))
        if year > max_year:
            max_year = year
            last_world_file = filename.replace("_", " ").strip()

    return last_world_file


def match_last_world_year(last_world_file) -> int | None:
    """
    death-rate-by-source-from-indoor-air-pollution,World,2021.svg
    """
    # match year
    y_match = re.match(r"^.*?,\s*(\d{4})\.svg$", last_world_file)
    if y_match:
        return int(y_match.group(1))

    return None


def find_last_world_file_from_owidslidersrcs(text) -> str | None:
    """ """
    # Parse the text using wikitextparser
    parsed = wtp.parse(text)

    # --- 1. Extract last_world_file from {{owidslidersrcs|gallery-World=...}}
    last_world_file = None
    for tpl in parsed.templates:
        if tpl.name.strip().lower() != "owidslidersrcs":
            continue

        if tpl.arguments:
            gallery = tpl.get_arg("gallery-World")
            if gallery:
                # matched = match_last_world_file(gallery.value.strip())
                matched = match_last_world_file_with_full_date(gallery.value.strip())
                if matched:
                    last_world_file = matched

        # break when match owidslidersrcs template
        break

    return last_world_file


__all__ = [
    "find_last_world_file_from_owidslidersrcs",
]
