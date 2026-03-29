""" """

from __future__ import annotations

import logging
import time

import mwclient

from ..utils.verify import verify_required_fields
from ..utils.wikitext import ensure_file_prefix
from .errors import RateLimitedError

logger = logging.getLogger(__name__)

_RETRY_DELAYS = (5, 15, 30)  # wait time in seconds between retry attempts


class MwClientPage:
    def __init__(self, title: str, site: mwclient.Site) -> None:
        self.title = title
        self.site = site
        self.load_page_error = ""
        self.page = None

    def load_page(self):
        if self.page:
            return self.page

        try:
            self.page = self.site.pages[self.title]
        except mwclient.errors.InvalidPageTitle:
            logger.warning(f"Title {self.title} is invalid")
            self.load_page_error = "invalidpagetitle"
            return False

        except Exception as exc:
            self.load_page_error = str(exc)
            logger.exception(f"Failed to load page {self.title}", exc_info=exc)
            return False

        return self.page

    def check_exists(self) -> bool:
        page = self.load_page()

        if not page or not page.exists:
            logger.warning(f"Title {self.title} does not exist")
            return False

        logger.info(f"Title {self.title} exists")
        return True

    def _edit(self, text, summary, page):
        try:
            page.edit(text, summary=summary)
        except mwclient.errors.APIError as exc:
            code = exc.code
            _info = exc.info
            if code == "ratelimited":
                raise RateLimitedError("You've exceeded your rate limit. Please wait some time and try again.") from exc

            raise
        except Exception as exc:
            logger.exception(f"Failed to edit page {self.title}", exc_info=exc)
            raise

    def _edit_with_retry(self, text: str, summary: str, page) -> None:
        """
        Attempt to edit a page with retry logic on rate limiting.
        Uses increasing delays between each attempt.
        """
        last_exc: Exception | None = None

        for attempt, delay in enumerate(_RETRY_DELAYS, start=1):
            try:
                page.edit(text, summary=summary)
                return  # edit succeeded
            except mwclient.errors.APIError as exc:
                if exc.code != "ratelimited":
                    raise  # different error, no need to retry

                last_exc = exc
                logger.warning(
                    f"Rate limited on attempt {attempt}/{len(_RETRY_DELAYS)} "
                    f"for page '{self.title}'. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)

        # all retry attempts exhausted
        raise mwclient.errors.APIError(
            "ratelimited",
            "Exceeded rate limit after all retry attempts.",
            {},
        ) from last_exc

    def edit_page(self, text: str, summary: str) -> dict[str, any]:
        page = self.load_page()

        if not page:
            return {"success": False, "error": self.load_page_error}

        try:
            self._edit(text, summary, page)
            return {"success": True}

        except mwclient.errors.EditError as exc:
            return {"success": False, "error": "editerror", "details": str(exc)}

        except mwclient.errors.ProtectedPageError as exc:
            details = {"code": exc.code, "info": exc.info}
            return {"success": False, "error": "protectedpageerror", "details": str(details)}

        except RateLimitedError:
            return {"success": False, "error": "ratelimited"}

        except mwclient.errors.APIError as exc:
            return {"success": False, "error": exc.code, "details": str(exc)}

        except Exception as exc:
            error_msg = str(exc)
            return {"success": False, "error": error_msg}


def is_page_exists(page_title: str, site: mwclient.Site) -> bool:
    return MwClientPage(page_title, site).check_exists()


def edit_page(site, title, text, summary) -> dict[str, any]:
    return MwClientPage(title, site).edit_page(text, summary)


def create_page(
    page_name: str,
    wikitext: str,
    site: mwclient.Site | None,
    summary: str = "",
) -> dict:
    """
    Create a new page on Wikimedia Commons.

    Args:
        page_name: The name of the page to create.
        wikitext: The wikitext content for the new page.
        site: Authenticated mwclient.Site object for Commons.
        summary: Edit summary.

    Returns:
        A dictionary with 'success' (bool) and optionally 'error' (str).
    """
    missing_fields = verify_required_fields(
        {
            "page_name": page_name,
            "wikitext": wikitext,
            "site": site,
        }
    )
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for create_page: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    return edit_page(site, page_name, wikitext, summary)


def update_file_text(
    original_file: str,
    updated_file_text: str,
    site: mwclient.Site | None,
) -> dict:
    """
    Update the wikitext of the original file to link to the cropped version.

    Args:
        original_file: The name of the original file on Commons.
        updated_file_text: The new wikitext for the original file.
        site: Authenticated mwclient.Site object for Commons.

    Returns:
        A dictionary with 'success' (bool) and optionally 'error' (str).
    """
    missing_fields = verify_required_fields(
        {
            "original_file": original_file,
            "updated_file_text": updated_file_text,
            "site": site,
        }
    )
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for update_file_text: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    original_file = ensure_file_prefix(original_file)

    summary = "Adding/updating {{Image extracted}}"

    return edit_page(site, original_file, updated_file_text, summary)


def update_page_text(
    page_name: str,
    updated_text: str,
    site: mwclient.Site | None,
    summary: str = "",
) -> dict:
    """
    Update the wikitext of any page on Wikimedia Commons.

    Args:
        page_name: The name of the page to update.
        updated_text: The new wikitext for the page.
        site: Authenticated mwclient.Site object for Commons.
        summary: Edit summary.

    Returns:
        A dictionary with 'success' (bool) and optionally 'error' (str).
    """
    missing_fields = verify_required_fields(
        {
            "page_name": page_name,
            "updated_text": updated_text,
            "site": site,
        }
    )
    if missing_fields:
        list_str = ", ".join(missing_fields)
        logger.error(f"Missing required fields for update_page_text: {list_str}")
        return {"success": False, "error": f"Missing required fields: {list_str}"}

    return edit_page(site, page_name, updated_text, summary)


def is_pages_exists(
    titles: list[str],
    site: mwclient.Site,
) -> dict[str, bool]:
    result = {}

    for i in range(0, len(titles), 50):
        group = titles[i : i + 50]

        group = [f"File:{file.removeprefix('File:')}" for file in group]

        json1 = site.get("query", titles="|".join(group))

        query = json1.get("query", {})

        normalized = {red["to"]: red["from"] for red in query.get("normalized", [])}

        query_pages = query.get("pages", {})
        for _, kk in query_pages.items():
            title = kk.get("title", "")
            if title:
                original_title = normalized.get(title, title)
                result[original_title] = "missing" not in kk

    return result


__all__ = [
    "create_page",
    "is_page_exists",
    "update_file_text",
    "update_page_text",
]
