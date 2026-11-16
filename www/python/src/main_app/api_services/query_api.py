"""MediaWiki API query operations.

Provides :class:`MediaWikiQueryService` for querying pages, templates,
categories, redirects, and links on a MediaWiki site, plus backward-compatible
legacy functions that accept a ``Site`` parameter.
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from mwclient.client import Site
from mwclient.errors import MwClientError

logger = logging.getLogger(__name__)


class MediaWikiQueryService:
    """Query a MediaWiki site for pages, templates, categories, redirects, and links.

    The ``site`` collaborator is injected once at construction time and reused
    for every query method.
    """

    def __init__(self, site: Site) -> None:
        self.site = site

    # ------------------------------------------------------------------
    # Template queries
    # ------------------------------------------------------------------

    def get_template_pages(
        self,
        title: str,
        namespace: str | int = "*",
    ) -> list[str]:
        """Return titles of pages that transclude *title*."""
        logger.debug(f"get_template_pages for template: {title=}, {namespace=}")
        params = {
            # "action": "query",
            "generator": "transcludedin",
            "gtinamespace": namespace,
            "gtilimit": "max",
            "formatversion": "2",
        }
        try:
            result = self.site.get("query", titles=title, **params)
        except (MwClientError, requests.exceptions.RequestException):
            logger.error(f"get_template_pages failed: {title=}")
            return []

        query_data = result.get("query", {})
        query_pages = query_data.get("pages", {})

        # { "pageid": 2973452, "ns": 100, "title": "title" }
        pages: list[str] = [x["title"] for x in query_pages]
        logger.info(f"find {len(pages)} pages.")
        return pages

    # ------------------------------------------------------------------
    # Page existence checks
    # ------------------------------------------------------------------

    def is_pages_exists(self, titles: list[str]) -> dict[str, bool]:
        """Check which of *titles* exist on the site.

        Note: if a batch fails, its titles are simply omitted from the result
        (not marked as missing). Callers relying on this for a fast-path filter
        (e.g. skipping a per-title existence check) must still verify
        individually before creating a page - see filter_created() /
        _process_one_item() in CreateOwidPagesWorker, which already does this.
        """
        result: dict[str, Any] = {}

        for i in range(0, len(titles), 50):
            group = titles[i : i + 50]
            try:
                json1 = self.site.get("query", titles="|".join(group))
            except (MwClientError, requests.exceptions.RequestException):
                logger.error(f"is_pages_exists failed for batch starting at index {i}")
                continue

            query_data = json1.get("query", {})
            normalized = {red["to"]: red["from"] for red in query_data.get("normalized", [])}

            query_pages = query_data.get("pages", {})
            for _, kk in query_pages.items():
                title = kk.get("title", "")
                if title:
                    original_title = normalized.get(title) or title
                    result[original_title] = "missing" not in kk

        return result

    # ------------------------------------------------------------------
    # Redirect resolution
    # ------------------------------------------------------------------

    def resolve_redirects(self, titles: list[str]) -> dict[str, dict[str, str]]:
        """Resolve redirects and normalizations for *titles*.

        Returns ``{"normalized": {to: from}, "from_to": {from: to}}``.
        """
        normalized: dict[str, Any] = {}
        from_to: dict[str, Any] = {}

        params = {
            "prop": "redirects",
            "redirects": 1,
            "converttitles": 1,
            "utf8": 1,
            "rdlimit": "max",
        }

        for i in range(0, len(titles), 50):
            group = titles[i : i + 50]

            try:
                data = self.site.get("query", titles="|".join(group), **params)
            except (MwClientError, requests.exceptions.RequestException):
                logger.error("resolve_redirects failed")
                continue

            query = data.get("query", {}) or {}

            for nor in query.get("normalized", []) or []:
                normalized[nor["to"]] = nor["from"]

            # Top-level redirects array: page is a redirect TO some target.
            for red in query.get("redirects", []) or []:
                from_to[red["from"]] = red["to"]

            # Per-page redirects array: pages that redirect TO this title.
            for page in (query.get("pages", {}) or {}).values():
                target = page.get("title", "")
                for t in page.get("redirects", []) or []:
                    from_to[t["title"]] = target

        return {
            "normalized": normalized,
            "from_to": from_to,
        }

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_pages(
        self,
        query: str,
        namespace: int = 0,
        limit: int | str = "max",
    ) -> list[str]:
        """Return page titles matching *query* via the MediaWiki search API."""
        params = {
            "list": "search",
            "srsearch": query,
            "srnamespace": str(namespace),
            "srlimit": str(limit),
            "srwhat": "text",
            "srsort": "just_match",
        }
        try:
            data = self.site.get("query", **params)
        except (MwClientError, requests.exceptions.RequestException):
            logger.error("search_pages failed")
            return []

        if not data:
            return []

        titles: list[str] = []
        query_data = data.get("query") or {}
        for item in query_data.get("search") or []:
            titles.append(item["title"])

        return titles

    # ------------------------------------------------------------------
    # Double redirects
    # ------------------------------------------------------------------

    def get_double_redirects(self) -> list[dict[str, str]]:
        """Return resolved double-redirect pairs ``[{"from", "to"}, ...]``.

        site API return example: {
            "batchcomplete": true,
            "limits": { "querypage": 5000 },
            "query": {
                "redirects": [
                    { "from": "WPM:Wiki Project Med/Board", "to": "WikiProjectMed:Wiki Project Med/Board" },
                    { "from": "WikiProjectMed:Wiki Project Med/Board", "to": "WikiProjectMed:Board" }
                ],
                "pages": [{
                    "pageid": 4669,
                    "ns": 4,
                    "title": "WikiProjectMed:Board",
                    "redirects": [
                        {
                            "pageid": 4846,
                            "ns": 4,
                            "title": "WikiProjectMed:Wiki Project Med/Board"
                        }
                    ]
                }]
            }
        }
        """
        params = {
            # "action": "query",
            "format": "json",
            "prop": "redirects",
            "generator": "querypage",
            "redirects": 1,
            "utf8": 1,
            "formatversion": "2",
            "gqppage": "DoubleRedirects",
            "gqplimit": "max",
            # "gqpoffset": "",
        }
        try:
            data = self.site.get("query", **params)
        except (MwClientError, requests.exceptions.RequestException):
            logger.error("Error querying redirects")
            return []

        if not data:
            return []

        query = data.get("query") or {}
        return query.get("redirects") or []

    # ------------------------------------------------------------------
    # Page links
    # ------------------------------------------------------------------

    def get_page_links(
        self,
        title: str,
        namespace: int = 0,
    ) -> dict[str, Any]:
        """Return wikilinks on *title* in *namespace*.

        Returns ``{"links": {title: {"ns", "title"}}, "normalized": [...], "redirects": [...]}``.
        """
        params = {
            "prop": "links",
            "titles": title,
            "plnamespace": str(namespace),
            "pllimit": "max",
            "converttitles": 1,
        }
        try:
            data = self.site.get("query", **params)
        except (MwClientError, requests.exceptions.RequestException):
            logger.error("get_page_links failed")
            return {}

        out: dict[str, Any] = {"links": {}, "normalized": [], "redirects": []}

        if not data:
            return out

        query = data.get("query", {}) or {}

        out["normalized"] = query.get("normalized", []) or []
        out["redirects"] = query.get("redirects", []) or []

        for page in (query.get("pages", {}) or {}).values():
            for link in page.get("links", []) or []:
                out["links"][link["title"]] = {"ns": link["ns"], "title": link["title"]}

        return out

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def import_page_from_wiki(
        self,
        title: str,
        family: str = "wikipedia",
    ) -> dict:
        """Import revision history of *title* from another wiki family.

        Uses the MediaWiki ``action=import`` API (interwiki import).
        Returns the API response dict.
        """
        params = {
            "action": "import",
            "title": title,
            "interwikisource": family,
            "fullhistory": 1,
        }
        try:
            result = self.site.post(**params)
            return result or {}
        except Exception as exc:
            logger.error("import_page_from_wiki failed for %s", title)
            return {"error": str(exc)}


__all__ = [
    "MediaWikiQueryService",
]
