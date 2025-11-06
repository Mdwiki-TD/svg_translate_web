"""

read temp.txt
get main title from {{SVGLanguages|parkinsons-disease-prevalence-ihme,World,1990.svg}} using wtp
get all files names from owidslidersrcs

"""

import wikitextparser as wtp
import re
from .utils.main_file import match_main_title_from_url, find_main_title


def get_titles_from_wikilinks(text):
    """
    Extracts:
      - all file links from text like:
        [[File:death rate from obesity, World, 2021 (cropped).svg|link=|thumb|upright=1.6|Death rate from obesity]]
    Returns: titles
    """
    parsed = wtp.parse(text)
    titles = []

    for link in parsed.wikilinks:
        if link.target.lower().endswith(".svg"):
            titles.append(link.target.strip())

    return titles


def get_titles(text, filter_duplicates=True):
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

            # Find all filenames inside this template (case-insensitive .svg)
            matches = re.findall(
                r"File:([^\n|!]+\.svg)", tpl.string, flags=re.IGNORECASE
            )

            titles.extend(m.strip() for m in matches)

    # titles.extend(get_titles_from_wikilinks(text))
    if filter_duplicates:
        titles = list(set(titles))

    return titles


def get_files_list(text, filter_duplicates=True):
    """
    Returns (main_title, titles).
    main_title:
      - From SVGLanguages: filename (no 'File:'), underscores -> spaces.
      - From Translate: 'File:...' string, underscores -> spaces.
    titles:
      - Filenames from all owidslidersrcs (no 'File:'), duplicates preserved.
    """
    titles = get_titles(text, filter_duplicates=filter_duplicates)

    main_title = find_main_title(text)

    if not main_title:
        main_title = match_main_title_from_url(text)

    if main_title:
        main_title = main_title.replace("_", " ").strip()

    return main_title, titles


__all__ = [
    "get_titles",
    "get_titles_from_wikilinks",
    "get_files_list",
]
