"""Wrapper around mwclient for editing, creating, and moving wiki pages."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

import mwclient

logger = logging.getLogger(__name__)

_RETRY_DELAYS = (5, 15, 30)  # wait time in seconds between retry attempts


def _handle_api_error(exc: Exception) -> dict[str, Any] | None:
    """Map common mwclient exceptions to a failure dict.

    Returns a ``{"success": False, ...}`` dict for known errors, or
    ``None`` if the exception is unrecognised (caller should log and
    handle it themselves).
    """
    if isinstance(exc, mwclient.errors.ProtectedPageError):
        return {"success": False, "error": "protectedpageerror", "details": str({"code": exc.code, "info": exc.info})}

    if isinstance(exc, mwclient.errors.EditError):
        return {"success": False, "error": "editerror", "details": str(exc)}

    if isinstance(exc, mwclient.errors.AssertUserFailedError):
        return {"success": False, "error": "assertuserfailed"}

    if isinstance(exc, mwclient.errors.UserBlocked):
        return {"success": False, "error": "userblocked"}

    if isinstance(exc, mwclient.errors.APIError):
        if exc.code == "ratelimited":
            return {"success": False, "error": "ratelimited"}
        return {"success": False, "error": exc.code, "details": str(exc)}

    return None  # unrecognised — let the caller log and handle


class MwClientPage:
    def __init__(self, title: str, site: mwclient.Site) -> None:
        self.title = title
        self.site = site
        self.load_page_error = ""
        self.page = None

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def _edit_page(self, page: mwclient.page.Page, text: str, summary: str, **kwargs) -> dict[str, Any]:
        try:
            save = page.edit(text, summary=summary, **kwargs) or {}
            return {"success": True, **save}
        except Exception as exc:
            result = _handle_api_error(exc)
            if result is not None:
                return result
            logger.exception(f"Failed to edit page '{self.title}'")
            return {"success": False, "error": str(exc)}

    def _move_page(
        self,
        page: mwclient.page.Page,
        new_title: str,
        reason: str,
        move_talk: bool = True,
        no_redirect: bool = False,
    ) -> dict[str, Any]:
        try:
            save = page.move(new_title, reason=reason, move_talk=move_talk, no_redirect=no_redirect) or {}
            return {"success": True, **save}
        except Exception as exc:
            result = _handle_api_error(exc)
            if result is not None:
                return result
            logger.exception(f"Failed to move page '{self.title}' -> '{new_title}'")
            return {"success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Unified retry logic
    # ------------------------------------------------------------------

    def _with_retry(self, operation: Callable[..., dict[str, Any]], *args, **kwargs) -> dict[str, Any]:
        """Call *operation* and retry up to len(_RETRY_DELAYS) times on rate-limit errors."""
        result = operation(*args, **kwargs)
        if result.get("error") != "ratelimited":
            return result

        for attempt, delay in enumerate(_RETRY_DELAYS, start=1):
            logger.warning(f"Rate limited (attempt {attempt}/{len(_RETRY_DELAYS)}). " f"Retrying in {delay}s...")
            time.sleep(delay)
            result = operation(*args, **kwargs)
            if result.get("error") != "ratelimited":
                return result

        return {"success": False, "error": "ratelimited"}

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def load_page(self) -> mwclient.page.Page | None:
        if self.page:
            return self.page

        try:
            self.page = self.site.pages[self.title]
        except mwclient.errors.InvalidPageTitle:
            logger.error(f"Title '{self.title}' is invalid")
            self.load_page_error = "invalidpagetitle"
            return None
        except Exception as exc:
            self.load_page_error = str(exc)
            logger.exception(f"Failed to load page '{self.title}'")
            return None

        return self.page

    def check_exists(self) -> bool:
        page = self.load_page()

        if not page:
            logger.warning(f"Failed to load page '{self.title}'")
            return False

        if not page.exists:
            logger.warning(f"Page '{self.title}' does not exist")
            return False

        logger.info(f"Page '{self.title}' exists")
        return True

    def is_redirect(self) -> bool:
        """Check if the page is a redirect using page.redirects_to()."""
        page = self.load_page()

        if not page or not page.exists:
            return False

        try:
            target = page.redirects_to()
            return target is not None
        except Exception as exc:
            logger.warning(f"Could not check redirect status of '{self.title}': {exc}")
            return False

    def edit_page(self, text: str, summary: str, nocreate: bool = True) -> dict[str, Any]:
        page = self.load_page()

        if not page:
            return {"success": False, "error": self.load_page_error}

        return self._with_retry(self._edit_page, page, text, summary, nocreate=nocreate)

    def create_page(self, text: str, summary: str) -> dict[str, Any]:
        page = self.load_page()

        if not page:
            return {"success": False, "error": self.load_page_error}

        if page.exists:
            return {"success": False, "error": "page exists"}

        return self._with_retry(self._edit_page, page, text, summary, createonly=True)

    def move_page(
        self,
        new_title: str,
        reason: str = "",
        move_talk: bool = True,
        no_redirect: bool = False,
    ) -> dict[str, Any]:
        """Move (rename) the page, with rate-limit retry handling."""
        page = self.load_page()

        if not page:
            return {"success": False, "error": self.load_page_error}

        if not page.exists:
            return {"success": False, "error": "missing"}

        return self._with_retry(self._move_page, page, new_title, reason, move_talk, no_redirect)
