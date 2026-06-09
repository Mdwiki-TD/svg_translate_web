import logging

import requests

from ..config import settings

logger = logging.getLogger(__name__)


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
        # "cmlimit": limit,
        "format": "json",
    }
    if limit is not None:
        params["cmlimit"] = limit

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
    "get_category_members_api",
]
