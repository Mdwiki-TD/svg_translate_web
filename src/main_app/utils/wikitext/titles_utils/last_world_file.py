""" """

import re

import wikitextparser as wtp


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
    Return:
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


def find_last_world_file_from_owidslidersrcs(text) -> str | None:
    """ """
    # Parse the text using wikitextparser
    parsed = wtp.parse(text)

    # --- 1. Extract last_world_file from {{owidslidersrcs|gallery-World=...}}
    last_world_file = None
    for tpl in parsed.templates:
        if tpl.name.strip().lower() == "owidslidersrcs":
            if tpl.arguments:
                gallery = tpl.get_arg("gallery-World")
                if gallery:
                    matched = match_last_world_file(gallery.value.strip())
                    if matched:
                        last_world_file = matched
            break
    return last_world_file


__all__ = [
    "find_last_world_file_from_owidslidersrcs",
]
