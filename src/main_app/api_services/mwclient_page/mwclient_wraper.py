"""Wrapper around mwclient for editing, creating, and moving wiki pages."""

from __future__ import annotations

import logging
import time
from typing import Any
from collections.abc import Callable

import mwclient
import mwclient.errors
from mwclient.client import Site
from mwclient.page import Page

from .mwclient_error import handle_mwclient_error

logger = logging.getLogger(__name__)

_RETRY_DELAYS = (5, 15, 30)  # wait time in seconds between retry attempts


class MwClientPage:
    def __init__(self, title: str, site: Site) -> None:
        self.title: str = title
        self.site: Site = site
        self.load_page_error: str = ""
        self.page: Page | None = None

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def load_page(self) -> Page | None:
        if self.page:
            return self.page

        try:
            self.page = self.site.pages[self.title]
        except mwclient.errors.InvalidPageTitle:
            logger.error("Title '%s' is invalid", self.title)
            self.load_page_error = "invalidpagetitle"
            return None
        except Exception as exc:
            self.load_page_error = str(exc)
            logger.exception("Failed to load page '%s'", self.title)
            return None

        return self.page

    def _edit_page(self, page: Page, text: str, summary: str, **kwargs) -> dict[str, Any]:
        try:
            save = page.edit(text, summary=summary, **kwargs) or {}
            return {"success": True, **save}
        except Exception as exc:
            result = handle_mwclient_error(exc)
            if result is not None:
                return result
            logger.exception("Failed to edit page '%s'", self.title)
            return {"success": False, "error": str(exc)}

    def _move_page(
        self,
        page: Page,
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
            logger.exception("Failed to move page '%s' -> '%s'", self.title, new_title)
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
            logger.warning("Rate limited (attempt %d/%d). Retrying in %ds...", attempt, len(_RETRY_DELAYS), delay)
            time.sleep(delay)
            result = operation(*args, **kwargs)
            if result.get("error") != "ratelimited":
                return result

        return {"success": False, "error": "ratelimited"}

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    @property
    def namespace(self) -> str | None:
        if not self.load_page() or not self.page:
            return None

        return self.page.namespace

    def exists(self) -> bool:
        if not self.load_page() or not self.page:
            logger.warning("Failed to load page '%s'", self.title)
            return False
        try:
            if not self.page.exists:
                logger.warning("Page '%s' does not exist", self.title)
                return False
        except Exception as exc:
            logger.warning("Could not check if page '%s' exists: %s", self.title, exc)
            return False

        logger.info("Page '%s' exists", self.title)
        return True

    def get_text(self) -> str:
        if not self.exists() or not self.page:
            return ""

        try:
            return self.page.text()
        except Exception:
            logger.exception("Failed to retrieve wikitext for %s", self.title)
        return ""

    def get_redirect_target(self) -> str | None:
        """Get the redirect target page name if the page is a redirect."""
        if not self.load_page() or not self.page:
            return None
        try:
            if not self.page.exists:
                return None
            target = self.page.redirects_to()
            return target.name if target is not None else None
        except Exception as exc:
            logger.debug("Could not get redirect of '%s': %s", self.title, exc)
            return None

    def is_redirect(self) -> bool:
        """Check if the page is a redirect using page.redirects_to()."""
        return self.get_redirect_target() is not None

    def edit(self, text: str, summary: str, nocreate: bool = True) -> dict[str, Any]:
        if text is None:
            return {"success": False, "error": "missing text"}

        if not self.load_page() or not self.page:
            return {"success": False, "error": self.load_page_error}

        return self._with_retry(self._edit_page, self.page, text, summary, nocreate=nocreate)

    def create(self, text: str, summary: str) -> dict[str, Any]:
        if not self.load_page() or not self.page:
            return {"success": False, "error": self.load_page_error}

        if self.page.exists:
            return {"success": False, "error": "page exists"}

        return self._with_retry(self._edit_page, self.page, text, summary, createonly=True)

    def move(
        self,
        new_title: str,
        reason: str = "",
        move_talk: bool = True,
        no_redirect: bool = False,
    ) -> dict[str, Any]:
        """Move (rename) the page, with rate-limit retry handling."""
        if not new_title:
            logger.error("Missing new_title for move page")
            return {"success": False, "error": "Missing new_title"}

        if not self.load_page() or not self.page:
            return {"success": False, "error": self.load_page_error}

        if not self.page.exists:
            return {"success": False, "error": "missing"}

        return self._with_retry(self._move_page, self.page, new_title, reason, move_talk, no_redirect)

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
