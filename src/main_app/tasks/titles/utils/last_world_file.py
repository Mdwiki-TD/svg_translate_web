""" """

import re

import wikitextparser as wtp


def match_last_world_file(text):
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

    text = text.value.strip().splitlines()[0].split("!")[0].strip()
    m = re.match(r"^File:[\w\-,.()\s_]+\.svg$", text)

    if not m:
        return ""

    last_world_file = text.replace("_", " ").strip()
    return last_world_file


def find_last_world_file_from_owidslidersrcs(text):
    """
    """
    # Parse the text using wikitextparser
    parsed = wtp.parse(text)

    # --- 1. Extract last_world_file from {{owidslidersrcs|gallery-World=...}}
    last_world_file = None
    for tpl in parsed.templates:
        if tpl.name.strip().lower() == "owidslidersrcs":
            if tpl.arguments:
                gallery = tpl.get_arg("gallery-World")
                if gallery:
                    last_world_file = match_last_world_file(gallery.value.strip())
            break
    return last_world_file


__all__ = [
    "find_last_world_file_from_owidslidersrcs",
]
