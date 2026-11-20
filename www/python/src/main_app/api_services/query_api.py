"""MediaWiki API query operations.

Provides :class:`MediaWikiQueryService` for querying pages, templates,
redirects, search results, and links on a MediaWiki site.

Design notes
------------
* The ``site`` collaborator is injected once and reused by every method.
* Every list-returning query follows MediaWiki continuation through a single
  helper (:meth:`MediaWikiQueryService._paginate`), so no method silently
  truncates its result at the first API batch.
* Error contract: request failures (``MwClientError`` / ``requests`` errors)
  are logged and, by default, yield whatever was collected so far.  Every
  public query accepts ``raise_on_error=True`` to re-raise instead, so a
  caller can tell a failed request apart from an empty result.
  ``get_page_assessments`` defaults to ``raise_on_error=True`` because a
  broken request must not be mistaken for "no assessments".
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Iterator, Sequence
from typing import Any

import requests
from mwclient.client import Site
from mwclient.errors import MwClientError

logger = logging.getLogger(__name__)

#: Exceptions that mean "the API request itself failed".
REQUEST_ERRORS: tuple[type[Exception], ...] = (
    MwClientError,
    requests.exceptions.RequestException,
)

Params = dict[str, Any]
Fetcher = Callable[[Params], dict[str, Any]]


class MediaWikiQueryService:
    """Query a MediaWiki site for pages, templates, redirects, search results, and links."""

    #: Maximum number of titles accepted per request (API limit for non-bot accounts).
    BATCH_SIZE = 50

    #: Hard cap on continuation rounds per query, so a misbehaving response
    #: can never turn into an endless request loop.
    MAX_CONTINUATION_ROUNDS = 50

    def __init__(self, site: Site) -> None:
        self.site = site

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_query(self, params: Params) -> dict[str, Any]:
        """Send an ``action=query`` request using HTTP GET."""
        return self.site.get("query", **params)

    def _post_query(self, params: Params) -> dict[str, Any]:
        """Send an ``action=query`` request through ``Site.api`` (HTTP POST, for long parameter lists)."""
        return self.site.api(action="query", **params)

    @staticmethod
    def _chunks(items: Sequence[str], size: int) -> Iterator[list[str]]:
        """Yield *items* in consecutive lists of at most *size* elements."""
        for start in range(0, len(items), size):
            yield list(items[start : start + size])

    @staticmethod
    def _iter_pages(query: dict[str, Any]) -> list[dict[str, Any]]:
        """Return ``query["pages"]`` as a list, for both formatversion 1 (dict) and 2 (list)."""
        pages = query.get("pages") or []
        return list(pages.values()) if isinstance(pages, dict) else list(pages)

    def _paginate(
        self,
        base_params: Params,
        label: str,
        fetch: Fetcher,
        *,
        raise_on_error: bool = False,
    ) -> Iterator[dict[str, Any]]:
        """Yield every response of a query, following MediaWiki continuation.

        The API signals "there is more" with a *dict of tokens*, e.g.
        ``{"continue": "-||userinfo", "pacontinue": "20423|571"}``. Every token
        must be sent back verbatim: keeping only the ``continue`` sentinel drops
        the module token, so the API repeats the same batch and the caller
        either loses data or loops forever.

        Iteration stops when a response carries no module token, when a token
        repeats (the server is not advancing), or after
        ``MAX_CONTINUATION_ROUNDS``.  On a request error the iteration ends
        with what was already yielded; with ``raise_on_error=True`` the error
        is re-raised instead.
        """
        request_params = dict(base_params)
        seen_tokens: set[tuple[Any, ...]] = set()

        for _ in range(self.MAX_CONTINUATION_ROUNDS):
            try:
                response = fetch(request_params) or {}
            except REQUEST_ERRORS:
                logger.exception("%s: API request failed", label)
                if raise_on_error:
                    raise
                return

            yield response

            continue_data = response.get("continue") or {}
            # Only module tokens (pacontinue, plcontinue, gticontinue, ...)
            # advance the query; "continue" itself is the "-||..." sentinel.
            tokens = {k: v for k, v in continue_data.items() if k != "continue"}
            if not tokens:
                return

            token_key = tuple(sorted(tokens.items()))
            if token_key in seen_tokens:
                logger.error(
                    "%s: continuation did not advance (tokens=%s); stopping to avoid an endless loop",
                    label,
                    tokens,
                )
                return
            seen_tokens.add(token_key)

            # Always rebuild from the base params so stale tokens never leak
            # into later requests.
            request_params = {**base_params, **continue_data}
        else:
            logger.warning("%s: stopped after %d continuation rounds", label, self.MAX_CONTINUATION_ROUNDS)

    @staticmethod
    def _merge_assessments(existing: dict[str, Any], incoming: dict[str, Any]) -> None:
        """Merge the ``pageassessments`` payload of *incoming* into *existing*.

        The same page can appear in several continuation batches, each carrying
        a different slice of its assessments (one entry per WikiProject).
        """
        extra = incoming.get("pageassessments")
        if not extra:
            return

        current = existing.get("pageassessments")
        if current is None:
            existing["pageassessments"] = extra
        elif isinstance(current, dict) and isinstance(extra, dict):
            current.update(extra)
        elif isinstance(current, list) and isinstance(extra, list):
            current.extend(extra)
        else:
            logger.warning(
                "Cannot merge pageassessments of types %s and %s for %r",
                type(current).__name__,
                type(extra).__name__,
                existing.get("title"),
            )

    # ------------------------------------------------------------------
    # Page assessments
    # ------------------------------------------------------------------

    def get_page_assessments(
        self,
        titles_list: Sequence[str],
        *,
        raise_on_error: bool = True,
    ) -> list[dict[str, Any]]:
        """Fetch page assessments for a list of titles.

        Titles are sent in batches of ``BATCH_SIZE``.  When a page's
        assessments are split across continuation batches they are merged into
        a single page dictionary.

        Args:
            titles_list: Page titles (any length).
            raise_on_error: Re-raise request failures (default) so callers such
                as ``AssessmentsSyncer.collect`` can report the chunk as failed
                instead of treating a broken request as "no assessments".

        Returns:
            One dictionary per page, with its assessment data.
        """
        if self.site is None:
            logger.warning("No site available for fetching assessments")
            return []

        logger.debug("Fetching assessments for %d titles", len(titles_list))

        pages_by_key: dict[Any, dict[str, Any]] = {}

        for group in self._chunks(titles_list, self.BATCH_SIZE):
            params: Params = {
                "prop": "pageassessments",
                "titles": "|".join(group),
                "utf8": 1,
                # palimit (not ellimit) is the pageassessments module limit; the
                # default is very low, so a 50-title batch would need many requests.
                "palimit": "max",
                "formatversion": 2,
            }
            # POST: 50 long titles can exceed practical URL length limits.
            for response in self._paginate(
                params,
                "get_page_assessments",
                self._post_query,
                raise_on_error=raise_on_error,
            ):
                for page in self._iter_pages(response.get("query") or {}):
                    key = page.get("pageid", page.get("title"))
                    existing = pages_by_key.get(key)
                    if existing is None:
                        pages_by_key[key] = page
                    else:
                        self._merge_assessments(existing, page)

        results = list(pages_by_key.values())
        logger.info("get_page_assessments returned %d pages for %d titles", len(results), len(titles_list))
        return results

    # ------------------------------------------------------------------
    # Template queries
    # ------------------------------------------------------------------

    def get_template_pages(
        self,
        title: str,
        namespace: str | int = "*",
        *,
        raise_on_error: bool = False,
    ) -> list[str]:
        """Return titles of pages that transclude *title* (``"*"`` means all namespaces)."""
        logger.debug("get_template_pages for template: title=%r, namespace=%r", title, namespace)
        params: Params = {
            "generator": "transcludedin",
            "titles": title,
            "gtilimit": "max",
            "formatversion": 2,
        }
        if str(namespace) != "*":
            params["gtinamespace"] = namespace

        # Example item: {"pageid": 2973452, "ns": 100, "title": "title"}
        pages: dict[str, None] = {}  # ordered set: keeps order, drops duplicates
        for result in self._paginate(params, "get_template_pages", self._get_query, raise_on_error=raise_on_error):
            for page in self._iter_pages(result.get("query") or {}):
                page_title = page.get("title")
                if page_title:
                    pages[page_title] = None

        logger.info("get_template_pages found %d pages for %r", len(pages), title)
        return list(pages)

    # ------------------------------------------------------------------
    # Page existence checks
    # ------------------------------------------------------------------

    def is_pages_exists(
        self,
        titles: Sequence[str],
        *,
        raise_on_error: bool = False,
    ) -> dict[str, bool]:
        """Check which of *titles* exist on the site.

        Keys are the titles exactly as the caller passed them (normalization
        such as ``a_b`` -> ``A b`` is mapped back).  Invalid titles are
        reported as non-existent.

        Note: if a batch fails (and ``raise_on_error`` is false), its titles
        are simply omitted from the result (not marked as missing). Callers
        relying on this for a fast-path filter (e.g. skipping a per-title
        existence check) must still verify individually before creating a
        page - see filter_created() / _process_one_item() in
        CreateOwidPagesWorker, which already does this.
        """
        logger.debug("is_pages_exists called with %d titles", len(titles))
        result: dict[str, bool] = {}

        for group in self._chunks(titles, self.BATCH_SIZE):
            requested = set(group)
            params: Params = {"titles": "|".join(group), "formatversion": 2}

            for data in self._paginate(params, "is_pages_exists", self._get_query, raise_on_error=raise_on_error):
                query = data.get("query") or {}

                # normalized: [{"from": "a_b", "to": "A b"}, ...]; several
                # inputs may normalize to the same title.
                origins: dict[str, list[str]] = defaultdict(list)
                for item in query.get("normalized") or []:
                    origins[item["to"]].append(item["from"])

                for page in self._iter_pages(query):
                    title = page.get("title")
                    if not title:
                        continue
                    # Test key presence: formatversion 1 reports flags as "" (falsy).
                    exists = "missing" not in page and "invalid" not in page
                    keys = list(origins.get(title, []))
                    if title in requested:
                        keys.append(title)
                    for key in keys:
                        result[key] = exists

        logger.info("is_pages_exists: %d/%d titles exist", sum(result.values()), len(titles))
        return result

    # ------------------------------------------------------------------
    # Redirect resolution
    # ------------------------------------------------------------------

    def resolve_redirects(
        self,
        titles: Sequence[str],
        *,
        raise_on_error: bool = False,
    ) -> dict[str, dict[str, str]]:
        """Resolve redirects and normalizations for *titles*.

        Returns ``{"normalized": {to: from}, "from_to": {from: to}}``.
        """
        logger.debug("resolve_redirects called with %d titles", len(titles))
        normalized: dict[str, str] = {}
        from_to: dict[str, str] = {}

        base_params: Params = {
            "prop": "redirects",
            "redirects": 1,
            "converttitles": 1,
            "utf8": 1,
            "rdlimit": "max",
            "formatversion": 2,
        }

        for group in self._chunks(titles, self.BATCH_SIZE):
            batch_params = {**base_params, "titles": "|".join(group)}

            for data in self._paginate(
                batch_params, "resolve_redirects", self._get_query, raise_on_error=raise_on_error
            ):
                query = data.get("query") or {}

                for nor in query.get("normalized") or []:
                    normalized[nor["to"]] = nor["from"]

                # Top-level redirects array: page is a redirect TO some target.
                for red in query.get("redirects") or []:
                    from_to[red["from"]] = red["to"]

                # Per-page redirects array: pages that redirect TO this title.
                for page in self._iter_pages(query):
                    target = page.get("title", "")
                    for redirect in page.get("redirects") or []:
                        from_to[redirect["title"]] = target

        logger.info(
            "resolve_redirects found %d normalizations and %d redirects",
            len(normalized),
            len(from_to),
        )
        return {"normalized": normalized, "from_to": from_to}

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_pages(
        self,
        query: str,
        namespace: int = 0,
        limit: int | str = "max",
        *,
        max_results: int | None = None,
        raise_on_error: bool = False,
    ) -> list[str]:
        """Return page titles matching *query* via the MediaWiki search API.

        Args:
            query: Search expression.
            namespace: Namespace number to search in.
            limit: Page size of each API request (``"max"`` for the largest allowed).
            max_results: Optional overall cap; no further requests are made once reached.
            raise_on_error: Re-raise request failures instead of returning partial results.
        """
        logger.debug(
            "search_pages called with query=%r, namespace=%s, limit=%s, max_results=%s",
            query,
            namespace,
            limit,
            max_results,
        )
        params: Params = {
            "list": "search",
            "srsearch": query,
            "srnamespace": str(namespace),
            "srlimit": str(limit),
            "srwhat": "text",
            "srsort": "just_match",
            "formatversion": 2,
        }

        titles: list[str] = []
        for data in self._paginate(params, "search_pages", self._get_query, raise_on_error=raise_on_error):
            for item in (data.get("query") or {}).get("search") or []:
                titles.append(item["title"])
            if max_results is not None and len(titles) >= max_results:
                titles = titles[:max_results]
                break

        logger.info("search_pages found %d results for query=%r", len(titles), query)
        return titles

    # ------------------------------------------------------------------
    # Double redirects
    # ------------------------------------------------------------------

    def get_double_redirects(self, *, raise_on_error: bool = False) -> list[dict[str, str]]:
        """Return resolved double-redirect pairs ``[{"from", "to"}, ...]``.

        Site API return example::

            {
                "batchcomplete": true,
                "limits": {"querypage": 5000},
                "query": {
                    "redirects": [
                        {"from": "WPM:Wiki Project Med/Board", "to": "WikiProjectMed:Wiki Project Med/Board"},
                        {"from": "WikiProjectMed:Wiki Project Med/Board", "to": "WikiProjectMed:Board"},
                    ],
                    "pages": [
                        {
                            "pageid": 4669,
                            "ns": 4,
                            "title": "WikiProjectMed:Board",
                            "redirects": [{"pageid": 4846, "ns": 4, "title": "WikiProjectMed:Wiki Project Med/Board"}],
                        }
                    ],
                },
            }
        """
        logger.debug("get_double_redirects called")
        params: Params = {
            "prop": "redirects",
            "generator": "querypage",
            "redirects": 1,
            "utf8": 1,
            "formatversion": 2,
            "gqppage": "DoubleRedirects",
            "gqplimit": "max",
        }

        seen: set[tuple[str, str]] = set()
        redirects: list[dict[str, str]] = []
        for data in self._paginate(params, "get_double_redirects", self._get_query, raise_on_error=raise_on_error):
            for item in (data.get("query") or {}).get("redirects") or []:
                pair = (item.get("from", ""), item.get("to", ""))
                if pair not in seen:
                    seen.add(pair)
                    redirects.append(item)

        logger.info("get_double_redirects found %d redirects", len(redirects))
        return redirects

    # ------------------------------------------------------------------
    # Page links
    # ------------------------------------------------------------------

    def get_page_links(
        self,
        title: str,
        namespace: int = 0,
        *,
        raise_on_error: bool = False,
    ) -> dict[str, Any]:
        """Return wikilinks on *title* in *namespace*.

        Returns ``{"links": {title: {"ns", "title"}}, "normalized": [...], "redirects": [...]}``.
        """
        params: Params = {
            "prop": "links",
            "titles": title,
            "plnamespace": str(namespace),
            "pllimit": "max",
            "converttitles": 1,
            "formatversion": 2,
        }
        out: dict[str, Any] = {"links": {}, "normalized": [], "redirects": []}

        for data in self._paginate(params, "get_page_links", self._get_query, raise_on_error=raise_on_error):
            query = data.get("query") or {}

            out["normalized"].extend(query.get("normalized") or [])
            out["redirects"].extend(query.get("redirects") or [])

            for page in self._iter_pages(query):
                for link in page.get("links") or []:
                    out["links"][link["title"]] = {"ns": link["ns"], "title": link["title"]}

        logger.info("get_page_links found %d links for title=%r", len(out["links"]), title)
        return out

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def import_page_from_wiki(
        self,
        title: str,
        family: str = "wikipedia",
    ) -> dict[str, Any]:
        """Import the revision history of *title* from another wiki (interwiki import).

        Uses the MediaWiki ``action=import`` API, which requires a CSRF token
        and takes the source page in ``interwikipage``.

        Returns the API response dict, or ``{"error": "<message>"}`` on failure.
        """
        try:
            result = self.site.post(
                "import",
                token=self.site.get_token("csrf"),
                interwikisource=family,
                interwikipage=title,
                fullhistory=1,
            )
        except REQUEST_ERRORS as exc:
            logger.error("import_page_from_wiki failed for %r: %s", title, exc)
            return {"error": str(exc)}

        return result or {}


__all__ = [
    "REQUEST_ERRORS",
    "MediaWikiQueryService",
]
