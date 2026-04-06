from __future__ import annotations

import logging
import time
from pathlib import Path

import mwclient
import mwclient.errors
import requests

logger = logging.getLogger(__name__)


def fix_file_name(file_name: str) -> str:
    file_name = file_name.strip()
    if file_name.lower().startswith("file:"):
        file_name = file_name[5:].lstrip()
    return file_name


def _err(message: str, error_details: str = "") -> dict[str, object]:
    return {"success": False, "error": message, "error_details": error_details}


def _check_kwargs(
    file_name: str,
    file_path: Path,
    site: mwclient.client.Site | None = None,
    new_file: bool = False,
):
    """
        Check if the kwargs are valid
    """

    if not site:
        return _err("No site provided")

    if not file_name:
        return _err("File name is required")

    if file_path is None:
        return _err("File path is None")

    file_path = Path(file_path)

    if not file_path.is_file():
        logger.error(f"File not found: {file_path}")
        return _err("File not found")

    file_name = fix_file_name(file_name)
    page = site.pages[f"File:{file_name}"]
    if not new_file:
        if not page.exists:
            logger.error(f"File {file_name} does not exist on Commons")
            return _err("File not found on Commons")
    else:
        if page.exists:
            logger.error(f"File {file_name} already exists on Commons")
            return _err("File already exists on Commons")

    return _err(None)


def _upload_file(
    file_name: str,
    file_path: Path,
    site: mwclient.client.Site | None = None,
    summary: str | None = None,
    description: str | None = None,
) -> dict[str, str] | dict:
    """
        Single upload attempt — returns a result dict, never raises.
    """
    file_name = fix_file_name(file_name)

    try:
        response = site_upload(file_name, file_path, site, summary, description)

        logger.debug(f"Successfully uploaded {file_name} to Wikimedia Commons")
        return {"success": True, "result": response.get("result", ""), "response": response, **response}

    except mwclient.errors.AssertUserFailedError:
        # Session expired or user assertion failed — no point retrying
        msg = "User assertion failed; session may have expired"
        logger.error(msg)
        return _err("assertuserfailed", msg)

    except mwclient.errors.UserBlocked:
        # User is blocked — no point retrying
        msg = "User is blocked from editing"
        logger.error(msg)
        return _err("userblocked", msg)

    except mwclient.errors.InsufficientPermission:
        msg = "User does not have sufficient permissions to upload"
        logger.error(msg)
        return _err("insufficientpermission", msg)

    except mwclient.errors.FileExists:
        logger.error("File already exists on Wikimedia Commons")
        return _err("fileexists", "File already exists")

    except mwclient.errors.MaximumRetriesExceeded:
        # mwclient's internal network retry budget exhausted
        msg = "Maximum network retries exceeded"
        logger.error(msg)
        return _err("maxretriesexceeded", msg)

    except requests.exceptions.Timeout as exc:
        logger.error("Request timed out while uploading file")
        return _err("timeout", str(exc))

    except requests.exceptions.ConnectionError as exc:
        logger.error("Connection error while uploading file")
        return _err("connectionerror", str(exc))

    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error occurred while uploading file")
        return _err("httperror", str(exc))

    except mwclient.errors.APIError as exc:
        if exc.code == "ratelimited":
            logger.debug("Rate limited during upload")
            return _err("ratelimited")

        if exc.code == "fileexists-no-change":
            logger.debug("Upload result: fileexists-no-change")
            return _err("fileexists-no-change")

        return _err(exc.code, exc.info)

    except Exception as exc:
        logger.exception(f"Unexpected error uploading {file_name}")
        return _err("unexpected", str(exc))


def site_upload(
    file_name: str,
    file_path: Path,
    site: mwclient.client.Site | None = None,
    summary: str | None = None,
    description: str | None = None,
):
    """
        Upload a file to the site.

        API doc: https://www.mediawiki.org/wiki/API:Upload

        Args:
            file_name: Destination file_name, don't include namespace prefix like 'File:'
            file_path: Path
            site: mwclient client Site
            summary: Upload comment summary.
            description: Wikitext for the file description page.

        Returns:
            JSON result from the API.

        Returns Examples:
            - {"result": "Success", "filename": "Test1x.jpeg", "imageinfo": {...}}
            - { "upload": { "result": "Warning", "warnings": {...}, "filekey": "x", "sessionkey": "x"}

            warnings Examples:
            - {"duplicate": ["...jpg"]}
            - {"badfilename": "..png", "exists": "..png", "nochange": { "timestamp": "..." }}

        Returns Examples with ignore=True:
        - {"result": "Success", "filename": "...", "warnings": {"exists": "CampaignEvents_edits_registration.png"}}

        Raises:
            TypeError
            mwclient.errors.AssertUserFailedError
            mwclient.errors.UserBlocked
            mwclient.errors.InsufficientPermission
            mwclient.errors.FileExists
            mwclient.errors.MaximumRetriesExceeded
            mwclient.errors.APIError
            requests.exceptions.HTTPError
            requests.exceptions.ConnectionError
            requests.exceptions.Timeout

    """
    with open(file_path, "rb") as f:
        # Perform the upload
        response = site.upload(
            # file=(os.path.basename(file_path), file_content, 'image/svg+xml'),
            file=f,
            description=description,
            filename=file_name,
            comment=summary or "",
            ignore=True,  # skip warnings like "file exists"
        )

    return response


def upload_file(
    file_name: str,
    file_path: Path,
    site: mwclient.client.Site | None = None,
    summary: str | None = None,
    description: str | None = None,
    new_file: bool = False,
) -> dict[str, str] | dict:
    """
    Upload a file to Wikimedia Commons using mwclient.

    Returns:
        dict with keys:
            - result (str): 'Success' on success
            - error (str | None): error code on failure
            - error_details (str): additional error info
    """
    _check = _check_kwargs(file_name, file_path, site, new_file)

    if _check["error"]:
        return _check

    upload_result = _upload_file(
        file_name,
        file_path,
        site,
        summary,
        description,
    )
    return upload_result


__all__ = [
    "upload_file",
]
