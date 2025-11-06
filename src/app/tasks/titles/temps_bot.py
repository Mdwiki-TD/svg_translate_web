"""

read temp.txt
get main title from {{SVGLanguages|parkinsons-disease-prevalence-ihme,World,1990.svg}} using wtp
get all files names from owidslidersrcs

"""

import wikitextparser as wtp
import re


def match_main_title(text):
    # Match lines starting with *'''Translate''': followed by a URL
    pattern = r"^\*'''Translate''':\s+https?://svgtranslate\.toolforge\.org/(File:[\w\-,.()]+\.svg)$"
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1) if match else None


def match_main_title_new(text):
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


def find_main_title(text):

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


def get_titles(text):
    """
    Extracts:
      - all file names from {{owidslidersrcs}}
    Returns: titles
    """
    # Parse the text using wikitextparser
    parsed = wtp.parse(text)

    # --- Extract all file names from {{owidslidersrcs|...}}
    titles = []
    for tpl in parsed.templates:
        if tpl.name.strip().lower() == "owidslidersrcs":
            # Find all filenames inside this template
            matches = re.findall(r"File:([^\n|!]+\.svg)", tpl.string)
            titles.extend(m.strip() for m in matches)

    return titles


def get_files_list(text):
    """
    Returns (main_title, titles).
    main_title:
      - From SVGLanguages: filename (no 'File:'), underscores -> spaces.
      - From Translate: 'File:...' string, underscores -> spaces.
    titles:
      - Filenames from all owidslidersrcs (no 'File:'), duplicates preserved.
    """
    titles = get_titles(text)

    main_title = find_main_title(text)

    if not main_title:
        main_title = match_main_title(text)

    if main_title:
        main_title = main_title.replace("_", " ").strip()

    return main_title, titles


__all__ = [
    "match_main_title",
    "find_main_title",
    "get_titles",
    "get_files_list",
]
