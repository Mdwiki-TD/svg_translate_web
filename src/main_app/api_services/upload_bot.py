import logging
from pathlib import Path

import mwclient
import requests

logger = logging.getLogger(__name__)


def fix_file_name(file_name) -> str:
    file_name = file_name.strip()
    if file_name.lower().startswith("file:"):
        file_name = file_name[5:].lstrip()
    return file_name


def site_upload(
    file_name: str,
    file_path: Path,
    site: mwclient.client.Site = None,
    summary: str = None,
    description: str = None,
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
            - {"exists": "..png", "nochange": {"timestamp": "..."}}

    Raises:
        TypeError
        mwclient.errors.InsufficientPermission
        requests.exceptions.HTTPError
        mwclient.errors.FileExists: The file already exists and `ignore` is `False`.
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


def _upload_file(
    file_name: str,
    file_path: Path,
    site: mwclient.client.Site = None,
    summary: str = None,
    description: str = None,
) -> dict[str, str] | dict:
    """
    Upload an SVG file to Wikimedia Commons using mwclient.
    """
    file_name = fix_file_name(file_name)

    try:
        response = site_upload(file_name, file_path, site, summary, description)

        logger.debug(f"Successfully uploaded {file_name} to Wikimedia Commons")
        return {"result": response.get("result", ""), **response}

    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error occurred while uploading file")
        return {"error": "HTTPError", "error_details": str(exc)}

    except mwclient.errors.FileExists:
        logger.error("File already exists on Wikimedia Commons")
        return {"error": "FileExists", "error_details": "File already exists"}

    except mwclient.errors.InsufficientPermission:
        logger.error("User does not have sufficient permissions to perform an action")
        return {
            "error": "InsufficientPermission",
            "error_details": "User does not have sufficient permissions to perform an action",
        }

    except Exception as e:
        # ---
        if "fileexists-no-change" in str(e):
            logger.debug("Upload result: fileexists-no-change")
            return {"error": "fileexists-no-change"}
        # ---
        if "ratelimited" in str(e):
            logger.debug("You've exceeded your rate limit. Please wait some time and try again.")
            return {"error": "ratelimited"}
        # ---
        logger.error(f"Unexpected error uploading {file_name} to Wikimedia Commons:")

        return {"error": "Unknown error occurred", "error_details": str(e)}


def _check_kwargs(
    file_name: str,
    file_path: Path,
    site: mwclient.client.Site = None,
    new_file: bool = False,
):

    if not site:
        return {"error": "No site provided"}

    if file_name is None:
        return {"error": "File name is None"}

    if file_path is None:
        return {"error": "file path is None"}

    file_name = fix_file_name(file_name)
    page = site.pages[f"File:{file_name}"]
    if not new_file:
        # Check if file exists
        if not page.exists:
            logger.error(f"Warning: File {file_name} not exists on Commons")
            return {"error": "File not found on Commons"}
    else:
        if page.exists:
            logger.error(f"Warning: File {file_name} already exists on Commons")
            return {"error": "File already exists on Commons"}

    file_path = Path(str(file_path))

    if not file_path.exists():
        # raise FileNotFoundError(f"File not found: {file_path}")
        logger.error(f"File not found: {file_path}")
        return {"error": "File not found on server"}

    return {"error": None}


def upload_file(
    file_name: str,
    file_path: Path,
    site: mwclient.client.Site = None,
    summary: str = None,
    description: str = None,
    new_file: bool = False,
) -> dict[str, str] | dict:
    """
    Upload an SVG file to Wikimedia Commons using mwclient.

    Returns:
        dict with keys:
            - result (str) `Success` or ``
            - error (str|None) on failure
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
