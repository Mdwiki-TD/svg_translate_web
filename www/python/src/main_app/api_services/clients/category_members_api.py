"""
MediaWiki API query operations for categories
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from mwclient.client import Site
from mwclient.errors import APIError

logger = logging.getLogger(__name__)


@dataclass
class CategoryMember:
    title: str
    ns: int | None = None
    revid: int | None = None


class CategoryMembersService:
    """
    Query a MediaWiki site for categories.
    The ``site`` collaborator is injected once at construction time and reused for every query method.
    """

    MAX_ITERATIONS = 100

    def __init__(self, site: Site) -> None:
        self.site = site

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

    def fetch_cats_members_api(
        self,
        cat: str,
        depth: int = 0,
        ns: int | None = None,
    ) -> list[CategoryMember]:
        if not cat.startswith("Category:"):
            cat = f"Category:{cat}"

        params: dict[str, str] = {
            "list": "categorymembers",
            "cmtitle": cat,
            "cmlimit": "max",
            "cmtype": "page|subcat",
            "prop": "revisions",
            "rvprop": "ids",
            "rvdir": "newer",
            "format": "json",
        }

        titles: list[CategoryMember] = []
        # Empty on the first request; afterwards holds the API's own continuation data
        continuation: dict[str, str] = {}

        for _ in range(self.MAX_ITERATIONS):
            data = self.site.get("query", **params, **continuation)

            members = data.get("query", {}).get("categorymembers", [])
            for page in members:
                title = page.get("title", "")
                if not title:
                    continue

                item = CategoryMember(
                    title=title,
                    ns=int(page.get("ns")) if page.get("ns") else None,
                )

                revisions = page.get("revisions") or []

                if revisions:
                    revid = revisions[0].get("revid", "")
                    if revid:
                        item.revid = int(revid)

                if ns is None or item.ns == ns:
                    titles.append(item)

            # The API signals "more results" by returning a "continue" dict
            continuation = data.get("continue") or {}
            if not continuation:
                break
        else:
            # Reached only if the loop never hit `break`
            logger.warning("fetch_cats_members_api: Hit maximum iterations for '%s'", cat)

        return titles

    @classmethod
    def load(cls, site: Site) -> CategoryMembersService:
        return cls(site=site)


__all__ = [
    "CategoryMembersService",
]
