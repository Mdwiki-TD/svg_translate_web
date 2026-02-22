"""

"""

import re
import urllib

import wikitextparser as wtp


def match_main_title_from_url(text):
    # Match lines starting with *'''Translate''': followed by a URL
    pattern = r"^\*'''Translat(?:e|ion)''':\s+https?://svgtranslate\.toolforge\.org/(File:[\w\-,.()\s_]+\.svg)$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1) if match else None


def match_main_title_from_url_new(text):
    """Return the SVG filename from the ``Translate`` line if present."""

    pattern = re.compile(
        r"^\*'''Translat(?:e|ion)''':\s+(?P<url>https?://svgtranslate\.toolforge\.org/[^\s]+)",
        flags=re.MULTILINE | re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        return None

    # Wikitext links may wrap the URL with characters such as [] or quotes.
    url = match.group("url").rstrip("]')\">}")

    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return None

    if parsed.netloc.lower() != "svgtranslate.toolforge.org":
        return None

    path = urllib.parse.unquote(parsed.path.lstrip("/"))
    if not path.lower().endswith(".svg"):
        return None

    return path


def find_main_title_from_template(text):
    # Parse the text using wikitextparser
    parsed = wtp.parse(text)

    # --- 1. Extract main title from {{SVGLanguages|...}}
    main_title = None
    for tpl in parsed.templates:
        if tpl.name.strip().lower() == "svglanguages":
            if tpl.arguments:
                main_title = tpl.arguments[0].value.strip()
            break
    if main_title:
        main_title = main_title.replace("_", " ").strip()

    return main_title


def find_main_title_from_owidslidersrcs(text):
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
        "File:youth mortality rate, World, 1950.svg"
    """
    # Parse the text using wikitextparser
    parsed = wtp.parse(text)

    # --- 1. Extract main title from {{owidslidersrcs|gallery-World=...}}
    main_title = None
    for tpl in parsed.templates:
        if tpl.name.strip().lower() == "owidslidersrcs":
            if tpl.arguments:
                gallery = tpl.get_arg("gallery-World")
                if gallery:
                    gallery = gallery.value.strip().splitlines()[0].split("!")[0].strip()
                    m = re.match(r"^File:[\w\-,.()\s_]+\.svg$", gallery)
                    if m:
                        main_title = gallery.replace("_", " ").strip()
            break
    return main_title


def find_main_title(text):
    main_title = (
        find_main_title_from_template(text)
        or match_main_title_from_url_new(text)
        or match_main_title_from_url(text)
        or find_main_title_from_owidslidersrcs(text)
    )

    if main_title:
        main_title = main_title.replace("_", " ").strip()

    return main_title


__all__ = [
    "match_main_title_from_url",
    "match_main_title_from_url_new",
    "find_main_title",
]
