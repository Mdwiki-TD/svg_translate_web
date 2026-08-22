""" """

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from flask import has_request_context, url_for
from werkzeug.routing import BuildError

logger = logging.getLogger(__name__)


@dataclass
class SidebarItem:
    """Sidebar menu item definition.

    The URL is resolved lazily via `resolve_href()`, at render time, rather
    than when the menu is built. This keeps `load_groups_menu()` free of any
    Flask request/app-context dependency, which in turn makes it safe to
    cache with `functools.lru_cache`.
    """

    id: str
    title: str
    icon: str | None = None
    endpoint: str | None = None
    endpoint_kwargs: dict = field(default_factory=dict)
    fallback_href: str = "#"
    link_target: str | None = None
    disabled: bool = False
    requires_admin: bool = True

    def resolve_href(self) -> str:
        """Resolve this item's URL. Falls back to a static path when there's
        no active request context, or when `url_for` fails to build the URL
        (e.g. the endpoint doesn't exist / its blueprint isn't registered).
        """
        if self.endpoint and has_request_context():
            try:
                return url_for(self.endpoint, **self.endpoint_kwargs)
            except BuildError:
                logger.warning("Could not build URL for endpoint '%s', using fallback href", self.endpoint)
        return self.fallback_href


@dataclass
class SidebarGroup:
    """Sidebar group item definition."""

    id: str
    title: str
    icon: str
    items: list[SidebarItem]


__all__ = [
    "SidebarItem",
    "SidebarGroup",
]
