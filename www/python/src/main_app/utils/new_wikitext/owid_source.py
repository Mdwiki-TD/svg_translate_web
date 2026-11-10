"""
Find the Our World in Data source URL in a template page.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse


class OwidSourceFinder:
    """Extracts and validates the OWID grapher URL from wikitext."""

    ALLOWED_HOSTS = {"ourworldindata.org", "www.ourworldindata.org"}
    URL_TRAILING_CHARS = "]')\">}"

    # ``*'''Source''': <url>``
    SOURCE_LINE_PATTERN = re.compile(
        r"^\s*\*'''Source''':\s+(?P<url>https?://(?:www\.)?ourworldindata\.org(?:/[^\s]*)?)",
        flags=re.M | re.I,
    )
    # ``* <url>``
    BULLET_LINE_PATTERN = re.compile(
        r"^\s*\*\s*(?P<url>https?://(?:www\.)?ourworldindata\.org(?:/[^\s]*)?)",
        flags=re.M | re.I,
    )

    @staticmethod
    def check_url(url: str) -> bool:
        """Return True when the URL host is an OWID host."""
        try:
            parsed = urlparse(url)
        except ValueError:
            return False

        return parsed.netloc.lower() in OwidSourceFinder.ALLOWED_HOSTS

    @classmethod
    def _find_with_pattern(cls, pattern: re.Pattern[str], wikitext: str) -> str:
        match = pattern.search(wikitext)

        if not match:
            return ""

        # Clean trailing characters sometimes present in wikitext links
        url = match.group("url").rstrip(OwidSourceFinder.URL_TRAILING_CHARS)

        if not cls.check_url(url):
            return ""

        # Return the full validated URL
        return url

    @classmethod
    def find_from_source_line(cls, wikitext: str) -> str:
        """
        Input:
            *'''Source''': https://ourworldindata.org/grapher/share-electricity-renewables
            *'''Translate''': https://svgtranslate.toolforge.org/File:Share_electricity_renewables,_World,_1985.svg
        Output:
            https://ourworldindata.org/grapher/share-electricity-renewables
        """
        return cls._find_with_pattern(
            OwidSourceFinder.SOURCE_LINE_PATTERN,
            wikitext,
        )

    @classmethod
    def find_from_bullet_line(cls, wikitext: str) -> str:
        """
        Input:
            * https://ourworldindata.org/grapher/share-electricity-renewables
        Output:
            https://ourworldindata.org/grapher/share-electricity-renewables
        """
        return cls._find_with_pattern(
            OwidSourceFinder.BULLET_LINE_PATTERN,
            wikitext,
        )

    @classmethod
    def find_template_source(cls, wikitext: str, check_grapher: bool = True) -> str:
        """Return the OWID source URL, or an empty string when none is found."""
        url = cls.find_from_source_line(wikitext) or cls.find_from_bullet_line(wikitext)
        if check_grapher and "/grapher/" not in url:
            return ""
        return url


__all__ = [
    "OwidSourceFinder",
]
