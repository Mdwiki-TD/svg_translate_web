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

    def check_url(self, url: str) -> bool:
        """Return True when the URL host is an OWID host."""
        try:
            parsed = urlparse(url)
        except ValueError:
            return False

        return parsed.netloc.lower() in self.ALLOWED_HOSTS

    def _find_with_pattern(self, pattern: re.Pattern[str], wikitext: str) -> str:
        match = pattern.search(wikitext)

        if not match:
            return ""

        # Clean trailing characters sometimes present in wikitext links
        url = match.group("url").rstrip(self.URL_TRAILING_CHARS)

        if not self.check_url(url):
            return ""

        return url

    def find_from_source_line(self, wikitext: str) -> str:
        """
        Input:
            *'''Source''': https://ourworldindata.org/grapher/share-electricity-renewables
        Output:
            https://ourworldindata.org/grapher/share-electricity-renewables
        """
        return self._find_with_pattern(self.SOURCE_LINE_PATTERN, wikitext)

    def find_from_bullet_line(self, wikitext: str) -> str:
        """
        Input:
            * https://ourworldindata.org/grapher/share-electricity-renewables
        Output:
            https://ourworldindata.org/grapher/share-electricity-renewables
        """
        return self._find_with_pattern(self.BULLET_LINE_PATTERN, wikitext)

    def find_template_source(self, wikitext: str, check_grapher: bool = True) -> str:
        """Return the OWID source URL, or an empty string when none is found."""
        url = self.find_from_source_line(wikitext) or self.find_from_bullet_line(wikitext)
        if check_grapher and "/grapher/" not in url:
            return ""
        return url


__all__ = [
    "OwidSourceFinder",
]
