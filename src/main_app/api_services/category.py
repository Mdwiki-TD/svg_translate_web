import logging

import mwclient
import mwclient.errors
from mwclient.client import Site

logger = logging.getLogger(__name__)


def get_category_members(
    site: Site,
    category_title: str,
    namespace: int = 0,
    limit: int | str | None = None,
) -> list[str]:
    """
    Retrieve all members of a specified category from a MediaWiki site.
    """
    logger.debug(f"load category members for {category_title}")
    try:
        category = site.pages[category_title]
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
    except mwclient.errors.APIError as e:
        logger.warning(f"API error getting category members for {category_title}: {e}")
        return []
    except KeyError as e:
        logger.warning(f"Key error in API response for {category_title}: {e}")
        return []


__all__ = [
    "get_category_members",
]
