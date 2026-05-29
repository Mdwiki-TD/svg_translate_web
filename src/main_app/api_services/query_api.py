""" """

from __future__ import annotations

import logging

import mwclient
import requests

from ..config import settings

logger = logging.getLogger(__name__)


def get_template_pages_newapi(
    title,
    namespace="*",
) -> list[str]:
    # ---
    logger.debug(f"get_template_pages for template: {title=}, {namespace=}")
    # ---
    params = {
        "action": "query",
        "titles": title,
        "generator": "transcludedin",
        "gtinamespace": namespace,
        "gtilimit": "max",
        "formatversion": "2",
    }
    # ---
    api = None  # get_api()
    results = api.NewApi().post_continue(params, "query", _p_="pages", p_empty=[])
    # ---
    # { "pageid": 2973452, "ns": 100, "title": "بوابة:سباق الدراجات الهوائية" }
    pages = [x["title"] for x in results]
    # ---
    logger.info(f"mdwiki_api.py : find {len(pages)} pages.")
    # ---
    return pages


def get_template_pages(
    title,
    namespace="*",
    site: mwclient.Site = None,
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

    result = site.get("query", titles=title, **params)
    query_data = result.get("query", {})
    query_pages = query_data.get("pages", {})

    # { "pageid": 2973452, "ns": 100, "title": "بوابة:سباق الدراجات الهوائية" }
    pages = [x["title"] for x in query_pages]
    # ---
    logger.info(f"find {len(pages)} pages.")
    # ---
    return pages


def is_pages_exists(
    titles: list[str],
    site: mwclient.Site,
) -> dict[str, bool]:
    result = {}

    for i in range(0, len(titles), 50):
        group = titles[i : i + 50]

        group = [f"File:{file.removeprefix('File:')}" for file in group]

        json1 = site.get("query", titles="|".join(group))

        query_data = json1.get("query", {})

        normalized = {red["to"]: red["from"] for red in query_data.get("normalized", [])}

        query_pages = query_data.get("pages", {})
        for _, kk in query_pages.items():
            title = kk.get("title", "")
            if title:
                original_title = normalized.get(title, title)
                result[original_title] = "missing" not in kk

    return result


def resolve_redirects(
    titles: list[str],
    site: mwclient.Site,
) -> dict[str, bool]:
    normalized = {}
    from_to = {}

    params = {
        "prop": "redirects",
        "redirects": 1,
        "converttitles": 1,
        "utf8": 1,
        "rdlimit": "max",
    }

    for i in range(0, len(titles), 50):
        group = titles[i : i + 50]
        data = site.get("query", titles="|".join(group), **params)
        query = data.get("query", {}) or {}

        for nor in query.get("normalized", []) or []:
            normalized[nor["to"]] = nor["from"]

        # Top-level redirects array: page is a redirect TO some target.
        for red in query.get("redirects", []) or []:
            from_to[red["from"]] = red["to"]

        # Per-page redirects array: pages that redirect TO this title.
        for page in (query.get("pages", {}) or {}).values():
            target = page.get("title", "")
            for src in page.get("redirects", []) or []:
                from_to[src["title"]] = target

    result = {
        "normalized": normalized,
        "from_to": from_to,
    }

    return result


def search_pages(
    query: str,
    site: mwclient.Site,
    namespace: int = 0,
    limit: int | str = "max",
) -> list[str]:
    """Return page titles matching *query* via the MediaWiki search API."""
    titles: list[str] = []
    params = {
        "list": "search",
        "srsearch": query,
        "srnamespace": str(namespace),
        "srlimit": str(limit),
        "srwhat": "text",
        "srsort": "just_match",
    }
    data = site.get("query", **params)
    if not data:
        return titles

    query_data = data.get("query") or {}
    for item in query_data.get("search") or []:
        titles.append(item["title"])

    return titles


def get_double_redirects(site: mwclient.Site) -> list[dict[str, str]]:
    """Return resolved double-redirect pairs ``[{"from", "to"}, ...]``."""
    params = {
        "prop": "info",
        "generator": "querypage",
        "redirects": 1,
        "utf8": 1,
        "gqppage": "DoubleRedirects",
        "gqplimit": "max",
    }
    data = site.get("query", **params)
    if not data:
        return []
    query = data.get("query") or {}
    return query.get("redirects") or []


def get_page_links(
    title: str,
    site: mwclient.Site,
    namespace: int = 0,
) -> dict:
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
    data = site.get("query", **params)
    out: dict = {"links": {}, "normalized": [], "redirects": []}
    if not data:
        return out

    query = data.get("query", {}) or {}
    out["normalized"] = query.get("normalized", []) or []
    out["redirects"] = query.get("redirects", []) or []
    for page in (query.get("pages", {}) or {}).values():
        for link in page.get("links", []) or []:
            out["links"][link["title"]] = {"ns": link["ns"], "title": link["title"]}
    return out


def get_wikitext(title, project="commons.wikimedia.org"):
    """
    Fetch raw wikitext of a page from Wikimedia projects.
    Args:
        title (str): Page title (e.g. 'Template:OWID/Parkinsons prevalence')
        project (str): Domain of wiki (default: commons.wikimedia.org)
    Returns:
        str: wikitext content or None if not found
    """
    api_url = f"https://{project}/w/api.php"
    session = requests.Session()
    session.headers.update({"User-Agent": settings.other.user_agent})
    # https://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles=Yemen&rvprop=content&formatversion=2&rvslots=main&format=json
    params = {
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "format": "json",
        "formatversion": "2",
        "rvslots": "*",
        "titles": title,
    }
    data = {}
    try:
        response = session.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Error: get_wikitext : {e}")

    # data example: {"query": {"pages": [{"pageid": 350939, "ns": 0, "title": "Yemen", "revisions": [{"slots": {"main": {"contentmodel": "wikitext", "contentformat": "text/x-wiki", "content": ""}}}]}], "batchcomplete": True}, }

    pages = data.get("query", {}).get("pages", [])
    for page in pages:
        revs = page.get("revisions")
        if revs:
            return revs[0].get("slots", {}).get("main", {}).get("content")

    return None


__all__ = [
    "get_template_pages",
    "get_double_redirects",
    "get_page_links",
    "is_pages_exists",
    "resolve_redirects",
    "search_pages",
    "get_wikitext",
]
