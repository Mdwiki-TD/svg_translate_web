from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any

import requests

from ..clients.commons_client import create_commons_session

logger = logging.getLogger(__name__)

ALL_II_PROPS = [
    "timestamp",
    "user",
    "metadata",
    "mediatype",
    "userid",
    "url",
    "uploadwarning",
    "thumburls",
    "thumbmime",
    "size",
    "sha1",
    "parsedcomment",
    "mime",
    "extmetadata",
    "commonmetadata",
    "dimensions",
    "comment",
    "canonicaltitle",
    "bitdepth",
    "archivename",
    "badfile",
]


@dataclass
class FileInfo:
    imageinfo: list[dict[str, Any]] | None = None
    error: str | None = None
    exists: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_file_info(
    prefixed_file_name: str,
    *,
    session: requests.Session | None = None,
    iiprops: list[str] | None = None,
) -> FileInfo:
    """
    Get file info from Commons API.
    """
    if iiprops:
        iiprops = [p for p in iiprops if p in ALL_II_PROPS]
    else:
        iiprops = ["metadata"]

    if not prefixed_file_name:
        return FileInfo(error="No file name provided")

    if not session:
        session = create_commons_session()

    # Define API endpoint and parameters
    url = "https://commons.wikimedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "titles": prefixed_file_name,
        "formatversion": "2",
        "iiprop": "|".join(iiprops),
    }

    try:
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as err:
        logger.exception("Commons API request failed for %s", prefixed_file_name)
        return FileInfo(error=f"API error: {err}")

    # { "batchcomplete": true, "query": { "pages": [ { "ns": 6, "title": "File:34", "missing": true, "imagerepository": "" } ] } }

    pages = data.get("query", {}).get("pages", [])
    if not pages:
        return FileInfo(error="Unexpected API response")

    page = pages[0]

    # Check if file exists
    if page.get("missing") and not page.get("known"):
        return FileInfo(error=f"File {page.get('title', prefixed_file_name)} does not exist.", exists=False)

    # Extract imageinfo array
    imageinfo = page.get("imageinfo", [])
    if not imageinfo:
        return FileInfo(error=f"imageinfo not found for {page.get('title')}", exists=True)

    return FileInfo(error=None, imageinfo=imageinfo, exists=True)


__all__ = [
    "get_file_info",
]
