from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import requests
from mwclient.client import Site

from ..clients.commons_client import create_commons_session
from .download_file_utils import download_one_file
from .upload_bot import upload_file

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


def download_svg_file(
    filename: str,
    temp_dir: Path,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Download SVG file and return file path or error info."""
    logger.info(f"Downloading file: {filename}")

    file_data = download_one_file(
        title=filename,
        out_dir=temp_dir,
        overwrite=True,
        session=session,
    )

    if file_data.get("result") != "success":
        return {
            "ok": False,
            "path": None,
            "error": "download_failed",
            "details": file_data,
        }
    return {
        "ok": True,
        "path": Path(file_data["path"]),
        "error": None,
        "details": {},
    }


def upload_fixed_svg(
    filename: str,
    file_path: Path,
    tags_fixed: int,
    site: Site,
    summary: str | None = None,
) -> dict[str, Any]:
    """Upload fixed SVG file to Commons."""

    logger.info(f"Uploading fixed file: {filename}")

    summary = summary or f"Fixed {tags_fixed} nested tag(s)"

    result = upload_file(
        file_name=filename,
        file_path=file_path,
        site=site,
        summary=summary,
    )
    result_status = result.get("result") or ""
    error_details = result.get("error_details", "")

    if result_status.lower() == "success":
        return {
            "ok": True,
            "error": None,
            "error_details": None,
            "msg": None,
            "result": result,
        }

    if error_details.get("error") == "fileexists-no-change" or result_status == "fileexists-no-change":
        return {
            "ok": None,
            "error": "skipped",
            "error_details": None,
            "msg": "File already exists with same content",
            "result": None,
        }

    return {
        "ok": False,
        "error": result.get("error", "upload_failed"),
        "error_details": error_details,
        "msg": None,
        "result": None,
    }


__all__ = [
    "get_file_info",
    "download_svg_file",
    "upload_fixed_svg",
]
