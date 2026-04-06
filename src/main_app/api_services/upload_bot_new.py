from __future__ import annotations

import logging
import time
from pathlib import Path

import mwclient
import mwclient.errors
import requests

logger = logging.getLogger(__name__)

_RETRY_DELAYS = (5, 15, 30)  # wait time in seconds between retry attempts


def fix_file_name(file_name: str) -> str:
    file_name = file_name.strip()
    if file_name.lower().startswith("file:"):
        file_name = file_name[5:].lstrip()
    return file_name


class UploadFile:
    def __init__(
        self,
        file_name: str,
        file_path: Path,
        site: mwclient.client.Site | None = None,
        summary: str | None = None,
        description: str | None = None,
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

    @staticmethod
    def _err(message: str, error_details: str = "") -> dict[str, object]:
        return {"success": False, "error": message, "error_details": error_details}

    def _check_kwargs(self) -> dict:
        """
        Check if the kwargs are valid
        """
        if not self.site:
            return self._err("No site provided")

        if not self.file_name:
            return self._err("File name is required")

        if self.file_path is None:
            return self._err("File path is None")

        file_path = Path(self.file_path)
        if not file_path.is_file():
            logger.error(f"File not found: {self.file_path}")
            return self._err("File not found")

        page = self.site.pages[f"File:{self.file_name}"]
        if not self.new_file:
            if not page.exists:
                logger.error(f"File {self.file_name} does not exist on Commons")
                return self._err("File not found on Commons")
        else:
            if page.exists:
                logger.error(f"File {self.file_name} already exists on Commons")
                return self._err("File already exists on Commons")

        return self._err(None)

    def _upload_file(self) -> dict:
        """
        Single upload attempt — returns a result dict, never raises.
        """
        try:
            response = self._site_upload()
            logger.debug(f"Successfully uploaded {self.file_name} to Wikimedia Commons")
            return {"success": True, "result": response.get("result", ""), "response": response}

        except mwclient.errors.AssertUserFailedError:
            # Session expired or user assertion failed — no point retrying
            msg = "User assertion failed; session may have expired"
            logger.error(msg)
            return self._err("assertuserfailed", msg)

        except mwclient.errors.UserBlocked:
            # User is blocked — no point retrying
            msg = "User is blocked from editing"
            logger.error(msg)
            return self._err("userblocked", msg)

        except mwclient.errors.InsufficientPermission:
            msg = "User does not have sufficient permissions to upload"
            logger.error(msg)
            return self._err("insufficientpermission", msg)

        except mwclient.errors.FileExists:
            logger.error("File already exists on Wikimedia Commons")
            return self._err("fileexists", "File already exists")

        except mwclient.errors.MaximumRetriesExceeded:
            # mwclient's internal network retry budget exhausted
            msg = "Maximum network retries exceeded"
            logger.error(msg)
            return self._err("maxretriesexceeded", msg)

        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out while uploading file")
            return self._err("timeout", str(exc))

        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error while uploading file")
            return self._err("connectionerror", str(exc))

        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP error occurred while uploading file")
            return self._err("httperror", str(exc))

        except mwclient.errors.APIError as exc:
            if exc.code == "ratelimited":
                logger.debug("Rate limited during upload")
                return self._err("ratelimited")

            if exc.code == "fileexists-no-change":
                logger.debug("Upload result: fileexists-no-change")
                return self._err("fileexists-no-change")

            return self._err(exc.code, exc.info)

        except Exception as exc:
            logger.exception(f"Unexpected error uploading {self.file_name}")
            return self._err("unexpected", str(exc))

    def _site_upload(self) -> dict:
        """
        Upload a file to the site.

        API doc: https://www.mediawiki.org/wiki/API:Upload


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
        with open(self.file_path, "rb") as f:
            response = self.site.upload(
                file=f,
                description=self.description,
                filename=self.file_name,
                comment=self.summary or "",
                ignore=True,  # skip warnings like "file exists"
            )

        return response

    def upload(self) -> dict:
        check = self._check_kwargs()
        if check["error"]:
            return check

        upload_result = self._upload_file()

        if upload_result.get("error") != "ratelimited":
            return upload_result

        # handle retry
        return self._upload_with_retry()

    def _upload_with_retry(self) -> dict:
        for attempt, delay in enumerate(_RETRY_DELAYS, start=1):
            logger.warning(
                f"Rate limited on upload attempt {attempt}/{len(_RETRY_DELAYS)} "
                f"for file '{self.file_name}'. Retrying in {delay}s..."
            )
            time.sleep(delay)

            upload_result = self._upload_file()

            if upload_result.get("error") != "ratelimited":
                return upload_result

        return self._err("ratelimited", "Exceeded rate limit after all retry attempts")


def upload_file_new(
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
    return UploadFile(file_name, file_path, site, summary, description, new_file).upload()


__all__ = [
    "upload_file_new",
]
