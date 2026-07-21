from typing import Any

import requests

from ..api_services import create_commons_session
from ..config import settings


def lang_code_category(langcode: str) -> str:
    data = {
        "ar": "Arabic-language SVG",
        "en": "English-language SVG",
    }
    return data.get(langcode)


def get_file_languages(file_name: str, session: requests.Session | None = None) -> dict[str, Any]:
    """
    Extracts available SVG translation languages for a given Commons file.

    :param file_name: Name of the file on Wikimedia Commons.
    :return: Dictionary containing 'error' message (if any) and 'langs' list.
    """
    if not file_name:

        return {"error": "Empty fileName", "langs": None}
    if not session:
        session = create_commons_session(settings.other.user_agent)

    # Normalize file name by stripping leading "File:" prefix
    normalized_name = file_name.strip().removeprefix("file:")

    # Define API endpoint and parameters
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": f"File:{normalized_name}",
        "prop": "imageinfo",
        "iiprop": "metadata",
        "formatversion": "2",
        "format": "json",
    }

    try:
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as err:
        return {"error": f"API error: {err}", "langs": None}

    pages = data.get("query", {}).get("pages", [])
    if not pages:
        return {"error": "Unexpected API response", "langs": None}

    page = pages[0]

    # Check if file exists
    if page.get("missing") and not page.get("known"):
        return {"error": f"File {page.get('title', normalized_name)} does not exist.", "langs": None}

    # Extract metadata array
    imageinfo = page.get("imageinfo", [])
    if not imageinfo:
        return {"error": f"Metadata not found for {page.get('title')}", "langs": None}

    metadata = imageinfo[0].get("metadata", [])
    if not metadata:
        return {"error": f"Metadata array empty for {page.get('title')}", "langs": None}

    # Convert list of dicts [{'name': ..., 'value': ...}] into a single dictionary
    meta = {item["name"]: item["value"] for item in metadata if "name" in item and "value" in item}

    translations = meta.get("translations", [])

    if isinstance(translations, list) and len(translations) > 0:
        # Extract language codes from translation entries
        langs_keys = [t["name"] for t in translations if isinstance(t, dict) and "name" in t]
        return {"error": None, "langs": langs_keys if langs_keys else ["en"]}

    return {"error": None, "langs": ["en"]}
