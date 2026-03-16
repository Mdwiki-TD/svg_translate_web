""" """

import re
import urllib.parse


def check_url(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return False

    if parsed.netloc.lower() not in {"ourworldindata.org", "www.ourworldindata.org"}:
        return False
    return True


def _find_template_source_2(wikitext: str) -> str:
    """
    Extract OWID source URL from wikitext.

    Input:
        * https://ourworldindata.org/grapher/share-electricity-renewables
    Output:
        https://ourworldindata.org/grapher/share-electricity-renewables
    """

    pattern2 = re.compile(
        r"^\s*\*\s*(?P<url>https?://(?:www\.)?ourworldindata\.org(?:/[^\s]*)?)",
        flags=re.MULTILINE | re.IGNORECASE,
    )

    match = pattern2.search(wikitext)

    if not match:
        return ""

    # Clean trailing characters sometimes present in wikitext links
    url = match.group("url").rstrip("]')\">}")

    if not check_url(url):
        return ""

    # Return the full validated URL
    return url


def _find_template_source(wikitext: str) -> str:
    """
    Extract OWID source URL from wikitext.

    Input:
        *'''Source''': https://ourworldindata.org/grapher/share-electricity-renewables
        *'''Translate''': https://svgtranslate.toolforge.org/File:Share_electricity_renewables,_World,_1985.svg
    Output:
        https://ourworldindata.org/grapher/share-electricity-renewables
    """

    pattern = re.compile(
        r"^\s*\*'''Source''':\s+(?P<url>https?://(?:www\.)?ourworldindata\.org(?:/[^\s]*)?)",
        flags=re.MULTILINE | re.IGNORECASE,
    )

    match = pattern.search(wikitext)

    if not match:
        return ""

    # Clean trailing characters sometimes present in wikitext links
    url = match.group("url").rstrip("]')\">}")

    if not check_url(url):
        return ""

    # Return the full validated URL
    return url


def find_template_source(wikitext: str) -> str:
    return _find_template_source(wikitext) or _find_template_source_2(wikitext)
