import logging
import time
from pathlib import Path

import mwclient
import requests

logger = logging.getLogger(__name__)

_RETRY_DELAYS = (5, 15, 30)  # wait time in seconds between retry attempts


def fix_file_name(file_name) -> str:
    file_name = file_name.strip()
    if file_name.lower().startswith("file:"):
        file_name = file_name[5:].lstrip()
    return file_name


class UploadFile:
    def __init__(
        self,
        file_name: str,
        file_path: Path,
        site: mwclient.client.Site = None,
        summary: str = None,
        description: str = None,
        new_file: bool = False,
    ) -> None:
        self.file_name = file_name
        self.site = site
        self.file_path = file_path
        self.summary = summary
        self.description = description
        self.new_file = new_file

        if self.file_name:
            self.file_name = fix_file_name(self.file_name)

    def _check_kwargs(self):

        if not self.site:
            return {"error": "No site provided"}

        if self.file_name is None:
            return {"error": "File name is None"}

        if self.file_path is None:
            return {"error": "file path is None"}

        page = self.site.pages[f"File:{self.file_name}"]
        if not self.new_file:
            # Check if file exists
            if not page.exists:
                logger.error(f"Warning: File {self.file_name} not exists on Commons")
                return {"error": "File not found on Commons"}
        else:
            if page.exists:
                logger.error(f"Warning: File {self.file_name} already exists on Commons")
                return {"error": "File already exists on Commons"}

        file_path = Path(str(self.file_path))

        if not file_path.exists():
            # raise FileNotFoundError(f"File not found: {file_path}")
            logger.error(f"File not found: {file_path}")
            return {"error": "File not found on server"}

        return {"error": None}

    def _upload_file(self) -> dict[str, str] | dict:
        """
        Upload an SVG file to Wikimedia Commons using mwclient.
        """

        try:
            response = self.site_upload()

            logger.debug(f"Successfully uploaded {self.file_name} to Wikimedia Commons")
            return {"result": response.get("result", ""), **response}

        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP error occurred while uploading file")
            return {"error": "HTTPError", "error_details": str(exc)}

        except mwclient.errors.FileExists:
            logger.error("File already exists on Wikimedia Commons")
            return {"error": "FileExists", "error_details": "File already exists"}

        except mwclient.errors.InsufficientPermission:
            msg = "User does not have sufficient permissions to perform an action"
            logger.error(msg)
            return {"error": "InsufficientPermission", "error_details": msg}

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
            logger.error(f"Unexpected error uploading {self.file_name} to Wikimedia Commons:")

            return {"error": "Unknown error occurred", "error_details": str(e)}

    def site_upload(self):
        """
        Upload a file to the site.

        API doc: https://www.mediawiki.org/wiki/API:Upload

        Args:
            self.file_name: Destination file_name, don't include namespace prefix like 'File:'
            self.file_path: Path
            self.site: mwclient client Site
            self.summary: Upload comment summary.
            self.description: Wikitext for the file description page.

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
        with open(self.file_path, "rb") as f:
            # Perform the upload
            response = self.site.upload(
                # file=(os.path.basename(file_path), file_content, 'image/svg+xml'),
                file=f,
                description=self.description,
                filename=self.file_name,
                comment=self.summary or "",
                ignore=True,  # skip warnings like "file exists"
            )

        return response

    def upload(self):

        _check = self._check_kwargs()

        if _check["error"]:
            return _check

        upload_result = self._upload_file()

        if upload_result.get("error") != "ratelimited":
            return upload_result

        # handle retry
        return self.edit_with_retry()

    def edit_with_retry(self):
        for attempt, delay in enumerate(_RETRY_DELAYS, start=1):

            logger.warning(
                f"Rate limited on upload attempt {attempt}/{len(_RETRY_DELAYS)} "
                f"for File '{self.file_name}'. Retrying in {delay}s..."
            )
            time.sleep(delay)

            upload_result = self._upload_file()

            if upload_result.get("error") != "ratelimited":
                return upload_result

        return {"success": False, "error": "ratelimited"}


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
    return UploadFile(file_name, file_path, site, summary, description, new_file).upload()


__all__ = [
    "upload_file",
]
