"""

"""

import re


import urllib.parse


def find_template_source(
    wikitext: str,
) -> str:
    """
    Input:
        *'''Source''': https://ourworldindata.org/grapher/share-electricity-renewables
        *'''Translate''': https://svgtranslate.toolforge.org/File:Share_electricity_renewables,_World,_1985.svg
    Output:
        https://ourworldindata.org/grapher/share-electricity-renewables
    """

    pattern = re.compile(
        r"^\s*\*'''Source''':\s+(?P<url>https?://(?:www\.)?ourworldindata\.org/[^\s]+)",
        flags=re.MULTILINE | re.IGNORECASE,
    )
    match = pattern.search(wikitext)
    if not match:
        return None

    # Wikitext links may wrap the URL with characters such as [] or quotes.
    url = match.group("url").rstrip("]')\">}")

    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return None

    if parsed.netloc.lower() not in {"ourworldindata.org", "www.ourworldindata.org"}:
        return None

    path = urllib.parse.unquote(parsed.path.lstrip("/"))

    return path
