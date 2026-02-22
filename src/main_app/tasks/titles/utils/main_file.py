"""

"""

import re
import urllib

import wikitextparser as wtp


def match_main_title_from_url(text):
    # Match lines starting with *'''Translate''': followed by a URL
    pattern = r"^\*'''Translate''':\s+https?://svgtranslate\.toolforge\.org/(File:[\w\-,.()]+\.svg)$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1) if match else None


def match_main_title_from_url_new(text):
    """Return the SVG filename from the ``Translate`` line if present."""

    pattern = re.compile(
        r"^\*'''Translate''':\s+(?P<url>https?://svgtranslate\.toolforge\.org/[^\s]+)",
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


def find_main_title(text):
    main_title = (
        find_main_title_from_template(text) or match_main_title_from_url_new(text) or match_main_title_from_url(text)
    )

    if main_title:
        main_title = main_title.replace("_", " ").strip()

    return main_title


__all__ = [
    "match_main_title_from_url",
    "match_main_title_from_url_new",
    "find_main_title",
]
