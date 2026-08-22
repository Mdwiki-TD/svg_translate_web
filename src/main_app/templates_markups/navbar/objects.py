""" """

import logging
import random
from dataclasses import dataclass, field

from flask import request, url_for
from markupsafe import Markup, escape

logger = logging.getLogger(__name__)

NAV_ITEM_CLASS = "nav-item col-lg-auto col-md-4 col-sm-6 col-6"


@dataclass
class NavLink:
    """
    Represents a single navigation link.
    """

    text: str
    icon: str
    path: str

    disabled: bool = False
    url_endpoint: str | None = None
    url_kwargs: dict = field(default_factory=dict)
    title: str | None = None
    static_url: str | None = None
    for_admin: bool = False
    link_target: str | None = None

    def __post_init__(self) -> None:
        self.title = self.title or self.text

    def get_url(self) -> str:
        if self.static_url:
            return self.static_url

        if not self.url_endpoint:
            return self.path

        return url_for(self.url_endpoint, **self.url_kwargs)

    def is_active(self) -> bool:
        if self.link_target:
            return False

        return bool(request and request.path and request.path.startswith(self.path))

    def render(self) -> Markup:
        active = self.is_active()
        active_class = " active fw-bold" if active else ""
        aria = ' aria-current="page"' if active else ""
        target_attrs = ' target="_blank" rel="noopener noreferrer"' if self.link_target else ""
        url = self.get_url()

        return Markup(
            '<a class="nav-link{active_class}" href="{url}"{aria}{target}'
            ' title="{title}">'
            '<i class="bi {icon}"></i> {text}'
            "</a>"
        ).format(
            active_class=active_class,
            url=escape(url),
            aria=Markup(aria),
            target=Markup(target_attrs),
            title=escape(self.title),
            icon=escape(self.icon),
            text=escape(self.text),
        )


@dataclass
class NavDropdown:
    """
    Represents a dropdown navigation item containing several NavLink items,
    e.g. an "Extract/Inject" menu grouping a few related sub-links.
    """

    text: str
    icon: str
    items: list[NavLink] = field(default_factory=list)
    dropdown_id: str = field(default_factory=lambda: f"navbarDarkDropdownMenuLink-{random.randint(1000, 9999)}")
    for_admin: bool = False
    disabled: bool = False

    def is_active(self) -> bool:
        return any(item.is_active() for item in self.items)

    # ---------- rendering helpers ----------
    def _wrap_li(self, inner_html) -> Markup:
        return Markup('<li class="{cls}">{inner}</li>').format(cls=NAV_ITEM_CLASS, inner=inner_html)

    def render(self) -> Markup:
        active_class = " active fw-bold" if self.is_active() else ""
        items = [item for item in self.items if not item.disabled]

        if not items:
            return Markup("")

        items_html = Markup("").join(self._wrap_li(item.render()) for item in items)

        return Markup(
            '<li class="dropdown {cls}">'
            '<a class="nav-link dropdown-toggle{active_class}" href="#" id="{dropdown_id}" role="button"'
            ' data-bs-toggle="dropdown" aria-expanded="false">'
            '<i class="bi {icon}"></i> {text}'
            "</a>"
            '<ul class="dropdown-menu" aria-labelledby="{dropdown_id}">{items}</ul>'
            "</li>"
        ).format(
            cls=NAV_ITEM_CLASS,
            active_class=active_class,
            dropdown_id=escape(self.dropdown_id),
            icon=escape(self.icon),
            text=escape(self.text),
            items=items_html,
        )


__all__ = [
    "NavLink",
    "NavDropdown",
    "NAV_ITEM_CLASS",
]
