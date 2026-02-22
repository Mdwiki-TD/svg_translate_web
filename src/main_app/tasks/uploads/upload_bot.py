import logging
from pathlib import Path

import mwclient
import requests

logger = logging.getLogger("svg_translate")


def upload_file(file_name, file_path, site=None, summary=None) -> dict[str, str] | dict:
    """
    Upload an SVG file to Wikimedia Commons using mwclient.
    """
    error_details = ""
    if not site:
        return {"error": "No site provided"}
    if file_name is None or file_path is None:
        return {"error": "File name or file path is None"}

    file_name = file_name.strip()
    if file_name.lower().startswith("file:"):
        file_name = file_name[5:].lstrip()

    # Check if file exists
    page = site.Pages[f"File:{file_name}"]

    if not page.exists:
        logger.error(f"Warning: File {file_name} not exists on Commons")
        return {"error": "File not found on Commons"}

    file_path = Path(str(file_path))

    if not file_path.exists():
        # raise FileNotFoundError(f"File not found: {file_path}")
        logger.error(f"File not found: {file_path}")
        return {"error": "File not found on server"}

    try:
        with open(file_path, "rb") as f:
            # Perform the upload
            response = site.upload(
                # file=(os.path.basename(file_path), file_content, 'image/svg+xml'),
                file=f,
                filename=file_name,
                comment=summary or "",
                ignore=True,  # skip warnings like "file exists"
            )

        logger.debug(f"Successfully uploaded {file_name} to Wikimedia Commons")
        return {"result": response.get("result", ""), **response}
    except requests.exceptions.HTTPError:
        logger.error("HTTP error occurred while uploading file")
        error_details = "HTTP error"
    except mwclient.errors.FileExists:
        logger.error("File already exists on Wikimedia Commons")
        error_details = "File already exists"
    except mwclient.errors.InsufficientPermission:
        logger.error("User does not have sufficient permissions to perform an action")
        error_details = "User does not have sufficient permissions to perform an action"
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
        logger.error(f"{e}")
        error_details = str(e)

    return {"error": "Unknown error occurred", "error_details": error_details}
