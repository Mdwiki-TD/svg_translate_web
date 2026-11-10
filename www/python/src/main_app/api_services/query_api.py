""" """

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from mwclient.client import Site
from mwclient.errors import APIError, MwClientError

logger = logging.getLogger(__name__)


def get_template_pages(
    title: str,
    site: Site,
    namespace: str | int = "*",
) -> list[str]:
    # ---
    logger.debug(f"get_template_pages for template: {title=}, {namespace=}")
    # ---
    params = {
        # "action": "query",
        "generator": "transcludedin",
        "gtinamespace": namespace,
        "gtilimit": "max",
        "formatversion": "2",
    }
    try:
        result = site.get("query", titles=title, **params)
    except (MwClientError, requests.exceptions.RequestException):
        logger.error(f"get_template_pages failed: {title=}")
        return []

    query_data = result.get("query", {})
    query_pages = query_data.get("pages", {})

    # { "pageid": 2973452, "ns": 100, "title": "title" }
    pages: list[str] = [x["title"] for x in query_pages]
    # ---
    logger.info(f"find {len(pages)} pages.")
    # ---
    return pages


def is_pages_exists(
    titles: list[str],
    site: Site,
) -> dict[str, bool]:
    """Check which of *titles* exist on *site*.

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
            json1 = site.get("query", titles="|".join(group))
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


def resolve_redirects(
    titles: list[str],
    site: Site,
) -> dict[str, dict[str, str]]:
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
            data = site.get("query", titles="|".join(group), **params)
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

    result = {
        "normalized": normalized,
        "from_to": from_to,
    }

    return result


def search_pages(
    query: str,
    site: Site,
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
        data = site.get("query", **params)
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


def get_double_redirects(site: Site) -> list[dict[str, str]]:
    """
    Return resolved double-redirect pairs ``[{"from", "to"}, ...]``.

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
        data = site.get("query", **params)
    except (MwClientError, requests.exceptions.RequestException):
        logger.error("Error querying redirects")
        return []

    if not data:
        return []

    query = data.get("query") or {}
    return query.get("redirects") or []


def get_page_links(
    title: str,
    site: Site,
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
        data = site.get("query", **params)
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


def get_category_members_titles(
    site: Site,
    category_name: str,
    namespace: int | None = None,
) -> list[str]:
    """
    Fetch all file titles from the OWID category using MediaWiki API with pagination.

    Returns:
        List of file titles (strings).
    """
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

    all_files = []
    first_request = True
    cmcontinue = None
    while first_request or cmcontinue is not None:
        first_request = False
        if len(all_files) % 1000 == 0:
            logger.info(f"loaded {len(all_files)} members")

        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        try:
            data = site.get("query", **params)
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


def import_page_from_wiki(
    site: Site,
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
        result = site.post(**params)
        return result or {}
    except Exception as exc:
        logger.error("import_page_from_wiki failed for %s", title)
        return {"error": str(exc)}


__all__ = [
    "get_template_pages",
    "get_page_links",
    "is_pages_exists",
    "resolve_redirects",
    "search_pages",
    "get_double_redirects",
    "get_category_members_titles",
    "import_page_from_wiki",
]
