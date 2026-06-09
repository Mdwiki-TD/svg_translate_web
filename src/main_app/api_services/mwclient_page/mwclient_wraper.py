"""Wrapper around mwclient for editing, creating, and moving wiki pages."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

import mwclient

from .mwclient_error import handle_mwclient_error

logger = logging.getLogger(__name__)

_RETRY_DELAYS = (5, 15, 30)  # wait time in seconds between retry attempts


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
            result = handle_mwclient_error(exc)
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
            result = handle_mwclient_error(exc)
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
            logger.warning(f"Rate limited (attempt {attempt}/{len(_RETRY_DELAYS)}). Retrying in {delay}s...")
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

    def exists(self) -> bool:
        page = self.load_page()

        if not page:
            logger.warning(f"Failed to load page '{self.title}'")
            return False

        if not page.exists:
            logger.warning(f"Page '{self.title}' does not exist")
            return False

        logger.info(f"Page '{self.title}' exists")
        return True

    def get_redirect_target(self) -> str | None:
        """Get the redirect target page name if the page is a redirect."""
        page = self.load_page()
        if not page:
            return None
        try:
            if not page.exists:
                return None
            target = page.redirects_to()
            return target.name if target is not None else None
        except Exception as exc:
            logger.debug(f"Could not get redirect of '{self.title}': {exc}")
            return None

    def is_redirect(self) -> bool:
        """Check if the page is a redirect using page.redirects_to()."""
        return self.get_redirect_target() is not None

    def edit(self, text: str, summary: str, nocreate: bool = True) -> dict[str, Any]:
        page = self.load_page()

        if not page:
            return {"success": False, "error": self.load_page_error}

        return self._with_retry(self._edit_page, page, text, summary, nocreate=nocreate)

    def create(self, text: str, summary: str) -> dict[str, Any]:
        page = self.load_page()

        if not page:
            return {"success": False, "error": self.load_page_error}

        if page.exists:
            return {"success": False, "error": "page exists"}

        return self._with_retry(self._edit_page, page, text, summary, createonly=True)

    def move(
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

    # ------------------------------------------------------------------
    # Aliases
    # ------------------------------------------------------------------

    def check_exists(self) -> bool:
        return self.exists()

    def move_page(
        self,
        new_title: str,
        reason: str = "",
        move_talk: bool = True,
        no_redirect: bool = False,
    ) -> dict[str, Any]:
        return self.move(
            new_title,
            reason,
            move_talk,
            no_redirect,
        )

    def edit_page(self, text: str, summary: str, nocreate: bool = True) -> dict[str, Any]:
        return self.edit(text, summary, nocreate)

    def create_page(self, text: str, summary: str) -> dict[str, Any]:
        return self.create(text, summary)


__all__ = [
    "MwClientPage",
]
