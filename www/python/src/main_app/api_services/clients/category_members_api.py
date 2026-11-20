"""MediaWiki API query operations for categories.

Provides :class:`CategoryMembersService` for listing the members of a category,
either as plain titles (through mwclient's ``Category`` object) or as
:class:`CategoryMember` records that include the current revision id.

Error contract: request failures are logged and, by default, yield whatever was
collected so far.  Pass ``raise_on_error=True`` to re-raise instead, so a caller
can tell a failed request apart from an empty category.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import requests
from mwclient.client import Site
from mwclient.errors import MwClientError

logger = logging.getLogger(__name__)

#: Exceptions that mean "the API request itself failed" (``APIError`` is a subclass of ``MwClientError``).
REQUEST_ERRORS: tuple[type[Exception], ...] = (
    MwClientError,
    requests.exceptions.RequestException,
)

CATEGORY_PREFIX = "Category:"


@dataclass
class CategoryMember:
    """A single category member."""

    title: str
    ns: int | None = None
    revid: int | None = None


class CategoryMembersService:
    """Query a MediaWiki site for the members of a category.

    The ``site`` collaborator is injected once at construction time and reused
    for every query method.
    """

    #: Hard cap on continuation rounds, so a misbehaving response can never
    #: turn into an endless request loop.
    MAX_ITERATIONS = 100

    def __init__(self, site: Site) -> None:
        self.site = site

    # ------------------------------------------------------------------
    # Titles only
    # ------------------------------------------------------------------

    def get_category_members(
        self,
        category_title: str,
        namespace: int = 0,
        limit: int | str | None = None,
        *,
        raise_on_error: bool = False,
    ) -> list[str]:
        """Return the titles of all members of *category_title* in *namespace*.

        Args:
            category_title: Full category title, e.g. ``"Category:Medicine"``.
            namespace: Namespace number to list.
            limit: Accepted for backward compatibility; currently ignored.
            raise_on_error: Re-raise request failures instead of returning ``[]``.
        """
        logger.debug("get_category_members for %r (namespace=%s)", category_title, namespace)
        try:
            category = self.site.pages[category_title]
            members = category.members(
                prop="ids|title",
                namespace=namespace,
                sort="sortkey",
                dir="asc",
                generator=True,
            )
            # Consuming the generator is what actually issues the API requests.
            return [p if isinstance(p, str) else p.name for p in members]
        except (*REQUEST_ERRORS, KeyError):
            logger.exception("get_category_members failed for %r", category_title)
            if raise_on_error:
                raise
            return []

    # ------------------------------------------------------------------
    # Members with revision ids
    # ------------------------------------------------------------------

    def fetch_cats_members_api(
        self,
        cat: str,
        depth: int = 0,
        ns: int | None = None,
        *,
        raise_on_error: bool = False,
    ) -> list[CategoryMember]:
        """Return the members of *cat* together with their current revid.

        ``generator=categorymembers`` is required for ``prop=info`` to have a
        page set to work on: with ``list=categorymembers`` the prop module is
        silently ignored by the API, so no revision data ever comes back.
        ``lastrevid`` is the current revision of the page.

        Duplicates across continuation batches are dropped (first one wins) and
        members keep the API's sort order within each batch.

        Args:
            cat: Category name, with or without the ``Category:`` prefix.
            depth: Accepted for backward compatibility; subcategories are
                returned as members, not expanded.
            ns: When given, only members in this namespace are returned.
            raise_on_error: Re-raise request failures instead of returning
                the members collected so far.
        """
        if not cat.lower().startswith(CATEGORY_PREFIX.lower()):
            cat = f"{CATEGORY_PREFIX}{cat}"

        params: dict[str, Any] = {
            "generator": "categorymembers",
            "gcmtitle": cat,
            "gcmlimit": "max",
            "gcmtype": "page|subcat",
            "prop": "info",
            "formatversion": 2,
        }
        if ns is not None:
            # Filter on the server to avoid fetching members we would discard.
            params["gcmnamespace"] = ns

        members: dict[str, CategoryMember] = {}  # keyed by title: ordered and de-duplicated

        for data in self._paginate(params, cat, raise_on_error=raise_on_error):
            pages = self._iter_pages(data)
            # "index" is the generator's sort position within this batch.
            pages.sort(key=lambda page: page.get("index", 0))

            for page in pages:
                title = page.get("title", "")
                if not title or title in members:
                    continue

                item = CategoryMember(
                    title=title,
                    # `ns` is 0 for the main namespace, so it must be tested
                    # against None - a truthiness check would drop it.
                    ns=int(page["ns"]) if page.get("ns") is not None else None,
                    revid=int(page["lastrevid"]) if page.get("lastrevid") else None,
                )

                # Kept as a safeguard in addition to the server-side filter.
                if ns is None or item.ns == ns:
                    members[title] = item

        logger.info("fetch_cats_members_api found %d members for %r", len(members), cat)
        return list(members.values())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _paginate(
        self,
        base_params: dict[str, Any],
        label: str,
        *,
        raise_on_error: bool = False,
    ) -> Iterator[dict[str, Any]]:
        """Yield every response of an ``action=query`` request, following continuation.

        The API signals "more results" with a dict of tokens, e.g.
        ``{"continue": "gcmcontinue||", "gcmcontinue": "page|ABC|123"}``; all of
        them are sent back verbatim.  Iteration stops when no module token is
        returned, when a token repeats (the server is not advancing), or after
        ``MAX_ITERATIONS`` rounds.
        """
        request_params = dict(base_params)
        seen_tokens: set[tuple[Any, ...]] = set()

        for _ in range(self.MAX_ITERATIONS):
            try:
                data = self.site.get("query", **request_params) or {}
            except REQUEST_ERRORS:
                logger.exception("%s: API request failed", label)
                if raise_on_error:
                    raise
                return

            yield data

            continue_data = data.get("continue") or {}
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

            request_params = {**base_params, **continue_data}
        else:
            logger.warning("%s: hit maximum iterations (%d)", label, self.MAX_ITERATIONS)

    @staticmethod
    def _iter_pages(data: dict[str, Any]) -> list[dict[str, Any]]:
        """Return ``query.pages`` as a new list, tolerating both formatversion shapes."""
        pages = (data.get("query") or {}).get("pages") or []
        if isinstance(pages, dict):
            return list(pages.values())
        return list(pages)

    @classmethod
    def load(cls, site: Site) -> CategoryMembersService:
        """Build a service bound to *site*."""
        return cls(site=site)


__all__ = [
    "REQUEST_ERRORS",
    "CategoryMember",
    "CategoryMembersService",
]
