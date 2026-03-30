""" """

from __future__ import annotations

import logging
import time

import mwclient

logger = logging.getLogger(__name__)

_RETRY_DELAYS = (5, 15, 30)  # wait time in seconds between retry attempts


class MwClientPage:
    def __init__(self, title: str, site: mwclient.Site) -> None:
        self.title = title
        self.site = site
        self.load_page_error = ""
        self.page = None

    def load_page(self) -> mwclient.page.Page | bool:
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

    def _edit_page(self, page: mwclient.page.Page, text: str, summary: str) -> dict[str, any]:

        try:
            page.edit(text, summary=summary)
            return {"success": True}

        except mwclient.errors.ProtectedPageError as exc:
            details = {"code": exc.code, "info": exc.info}
            return {"success": False, "error": "protectedpageerror", "details": str(details)}

        except mwclient.errors.EditError as exc:
            return {"success": False, "error": "editerror", "details": str(exc)}

        except mwclient.errors.AssertUserFailedError:
            return {"success": False, "error": "assertuserfailed"}

        except mwclient.errors.UserBlocked:
            return {"success": False, "error": "userblocked"}

        except mwclient.errors.APIError as exc:
            if exc.code == "ratelimited":
                return {"success": False, "error": "ratelimited"}

            return {"success": False, "error": exc.code, "details": str(exc)}

        except Exception as exc:
            logger.exception(f"Failed to edit page {self.title}", exc_info=exc)
            return {"success": False, "error": str(exc)}

    def edit_page(self, text: str, summary: str) -> dict[str, any]:
        page = self.load_page()

        if not page:
            return {"success": False, "error": self.load_page_error}

        edit_result = self._edit_page(page, text, summary=summary)

        if edit_result.get("error") != "ratelimited":
            return edit_result

        # handle retry
        return self.edit_with_retry(page, text, summary)

    def edit_with_retry(self, page: mwclient.page.Page, text: str, summary: str) -> dict[str, any]:
        for attempt, delay in enumerate(_RETRY_DELAYS, start=1):

            logger.warning(
                f"Rate limited on attempt {attempt}/{len(_RETRY_DELAYS)} "
                f"for page '{self.title}'. Retrying in {delay}s..."
            )
            time.sleep(delay)

            edit_result = self._edit_page(page, text, summary=summary)

            if edit_result.get("error") != "ratelimited":
                return edit_result

        return {"success": False, "error": "ratelimited"}
