import logging

import mwclient
import requests

from ..config import settings

logger = logging.getLogger(__name__)


def get_category_members(
    site: mwclient.Site,
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

def get_category_members_api(category, project, limit=None):
    """
    Fetch all pages belonging to a given category from a Wikimedia project.

    Args:
        category (str): Category title
        project (str): Domain of wiki
        limit (int): Maximum results per request (max 500 for normal users, 5000 for bots)

    Returns:
        list[str]: List of page titles in the category
    """

    api_url = f"https://{project}/w/api.php"
    session = requests.Session()
    session.headers.update({"User-Agent": settings.other.user_agent})

    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category,
        "format": "json",
    }
    params["cmlimit"] = limit if limit is not None else "max"

    pages = []
    try:
        while True:
            response = session.get(api_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            members = data.get("query", {}).get("categorymembers", [])
            pages.extend([m["title"] for m in members])

            if "continue" in data:
                params["cmcontinue"] = data["continue"]["cmcontinue"]
            else:
                break
    except requests.exceptions.RequestException as e:
        logger.error("Failed to fetch category members: %s", e)
    else:
        logger.debug(f"Found {len(pages)} pages in category {category}")

    return pages


__all__ = [
    "get_category_members",
    "get_category_members_api",
]
