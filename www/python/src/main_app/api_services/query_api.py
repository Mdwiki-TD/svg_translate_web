"""MediaWiki API query operations.

Provides :class:`MediaWikiQueryService` for querying pages, templates,
categories, redirects, and links on a MediaWiki site, plus backward-compatible
legacy functions that accept a ``Site`` parameter.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from mwclient.client import Site
from mwclient.errors import APIError, MwClientError

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
    # Category members
    # ------------------------------------------------------------------

    def get_category_members_titles(
        self,
        category_name: str,
        namespace: int | None = None,
    ) -> list[str]:
        """Fetch all member titles from *category_name* with pagination."""
        page_count = 0
        delay = 0.1  # seconds
        max_delay = 8.0

        logger.info(f"Starting to fetch files from {category_name}")

        params = {
            # "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": category_name,
            # "cmtype": "file",
            "cmlimit": "max",
        }

        if namespace is not None:
            if namespace == 14:
                params["cmtype"] = "subcat"
            elif namespace == 6:
                params["cmtype"] = "file"
            else:
                params["cmnamespace"] = str(namespace)

        all_files: list[str] = []
        first_request = True
        cmcontinue = None
        while first_request or cmcontinue is not None:
            first_request = False
            if len(all_files) % 1000 == 0:
                logger.info(f"loaded {len(all_files)} members")

            if cmcontinue:
                params["cmcontinue"] = cmcontinue

            try:
                data = self.site.get("query", **params)
                members = data.get("query", {}).get("categorymembers", [])
                all_files.extend([x.get("title", "") for x in members])
                page_count += 1

                logger.debug(f"Fetched category members {page_count}: {len(members)} page, (total: {len(all_files)})")

                if "continue" in data:
                    cmcontinue = data["continue"].get("cmcontinue")
                    time.sleep(delay)
                else:
                    break

            except APIError as e:
                if e.code == "invalidcategory":
                    logger.warning(f"Invalid category: {category_name}")
                    break

            except Exception:
                logger.error("API request failed")
                if delay < max_delay:
                    delay = min(delay * 2, max_delay)
                    time.sleep(delay)
                    continue

        logger.info(f"Finished fetching {len(all_files)} files in {page_count} pages")
        return all_files

    def get_category_members(
        self,
        category_title: str,
        namespace: int = 0,
        limit: int | str | None = None,
    ) -> list[str]:
        """Retrieve all members of a specified category from a MediaWiki site."""
        logger.debug(f"load category members for {category_title}")
        try:
            category = self.site.pages[category_title]
            # Use list comprehension for efficiency - consumes the generator
            members = category.members(
                prop="ids|title",
                namespace=namespace,
                sort="sortkey",
                dir="asc",
                start=None,
                end=None,
                generator=True,
            )
            list_members = list(members)
            return [p if isinstance(p, str) else p.name for p in list_members]
        except APIError as e:
            logger.warning(f"API error getting category members for {category_title}: {e}")
            return []
        except KeyError as e:
            logger.warning(f"Key error in API response for {category_title}: {e}")
            return []

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


# ---------------------------------------------------------------------------
# Legacy compatibility layer — no business logic, delegates to MediaWikiQueryService
# ---------------------------------------------------------------------------


def get_template_pages(
    title: str,
    site: Site,
    namespace: str | int = "*",
) -> list[str]:
    """Legacy entry point. Use :meth:`MediaWikiQueryService.get_template_pages` instead."""
    return MediaWikiQueryService(site=site).get_template_pages(title, namespace)


def is_pages_exists(
    titles: list[str],
    site: Site,
) -> dict[str, bool]:
    """Legacy entry point. Use :meth:`MediaWikiQueryService.is_pages_exists` instead."""
    return MediaWikiQueryService(site=site).is_pages_exists(titles)


def resolve_redirects(
    titles: list[str],
    site: Site,
) -> dict[str, dict[str, str]]:
    """Legacy entry point. Use :meth:`MediaWikiQueryService.resolve_redirects` instead."""
    return MediaWikiQueryService(site=site).resolve_redirects(titles)


def search_pages(
    query: str,
    site: Site,
    namespace: int = 0,
    limit: int | str = "max",
) -> list[str]:
    """Legacy entry point. Use :meth:`MediaWikiQueryService.search_pages` instead."""
    return MediaWikiQueryService(site=site).search_pages(query, namespace, limit)


def get_double_redirects(site: Site) -> list[dict[str, str]]:
    """Legacy entry point. Use :meth:`MediaWikiQueryService.get_double_redirects` instead."""
    return MediaWikiQueryService(site=site).get_double_redirects()


def get_page_links(
    title: str,
    site: Site,
    namespace: int = 0,
) -> dict[str, Any]:
    """Legacy entry point. Use :meth:`MediaWikiQueryService.get_page_links` instead."""
    return MediaWikiQueryService(site=site).get_page_links(title, namespace)


def get_category_members_titles(
    site: Site,
    category_name: str,
    namespace: int | None = None,
) -> list[str]:
    """Legacy entry point. Use :meth:`MediaWikiQueryService.get_category_members_titles` instead."""
    return MediaWikiQueryService(site=site).get_category_members_titles(category_name, namespace)


def import_page_from_wiki(
    site: Site,
    title: str,
    family: str = "wikipedia",
) -> dict:
    """Legacy entry point. Use :meth:`MediaWikiQueryService.import_page_from_wiki` instead."""
    return MediaWikiQueryService(site=site).import_page_from_wiki(title, family)


__all__ = [
    "MediaWikiQueryService",
    "get_template_pages",
    "get_page_links",
    "is_pages_exists",
    "resolve_redirects",
    "search_pages",
    "get_double_redirects",
    "get_category_members_titles",
    "import_page_from_wiki",
]
