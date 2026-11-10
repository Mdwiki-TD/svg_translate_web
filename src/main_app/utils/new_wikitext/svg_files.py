"""
Collect SVG file titles from a page that uses ``{{owidslidersrcs}}`` and wikilinks.
"""

from __future__ import annotations

import re
from typing import Any

import wikitextparser as wtp

from .main_title_finder import MainTitleFinder


class SvgFilesCollector:
    """Collects SVG file names and the main title of a page."""

    def __init__(self, title_finder: MainTitleFinder | None = None) -> None:
        self.title_finder = title_finder or MainTitleFinder()

    def get_titles_from_wikilinks(self, text: str) -> list:
        """
        Return the SVG names of file links like
        ``[[File:Death rate from obesity, World, 2021 (cropped).svg|thumb|...]]``.
        """
        parsed = wtp.parse(text)
        titles: list[Any] = []

        for link in parsed.wikilinks:
            target = link.target
            if target.lower().endswith(".svg") and target.startswith("File:"):
                target = target[5:]
                titles.append(target.strip())

        return titles

    def get_titles(self, text: str, filter_duplicates: bool = True) -> list[str]:
        """Return all SVG file names found inside ``{{owidslidersrcs}}`` templates."""
        parsed = wtp.parse(text)

        titles: list[Any] = []

        for tpl in parsed.templates:
            if tpl.name.strip().lower() == "owidslidersrcs":
                # Find all filenames inside this template (case-insensitive .svg)
                matches = re.findall(r"File:([^\n|!]+\.svg)", tpl.string, flags=re.I)

                titles.extend(m.strip() for m in matches)

        if filter_duplicates:
            titles = list(set(titles))

        return titles

    def get_files_list_data(self, text: str, filter_duplicates: bool = True) -> dict[str, Any]:
        """Return ``{"main_title": ..., "titles": [...]}`` for the page."""
        titles = self.get_titles(text, filter_duplicates=filter_duplicates)
        titles.extend(self.get_titles_from_wikilinks(text))

        if filter_duplicates:
            titles = list(set(titles))

        main_title = self.title_finder.find_main_title(text)

        return {"main_title": main_title, "titles": titles}

    def count_svg_files(self, text: str) -> int:
        """Return the number of unique SVG files on the page."""
        data = self.get_files_list_data(text, filter_duplicates=True)
        return len(data["titles"])


__all__ = [
    "SvgFilesCollector",
]
