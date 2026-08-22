"""
navbar.py
---------
A Navbar object that auto-generates the navigation bar HTML, replacing
the manual Jinja macros (nav_link and nav_link_with_args) that used to
live in navbar.html.

Usage in the template after registering via init_app(app):

    {{ navbar.render_main_links(is_admin=is_admin) }}
    {{
        navbar.render_user_links(
            profile_url = url_for("profile.dashboard", user_name=current_username),
            current_username = current_username
        )
    }}

Both methods return a safe Markup object (no need for the |safe filter,
though adding it doesn't hurt).
"""

import logging
from urllib.parse import quote

from flask import request, url_for
from markupsafe import Markup, escape

from .objects import NAV_ITEM_CLASS, NavDropdown, NavLink

logger = logging.getLogger(__name__)


class NavigationBar:

    def __init__(self, links=None) -> None:
        # A single ordered list holds NavLink and NavDropdown entries
        # (regular, admin-only, or grouped); order in this list is render order.
        self.links = []
        for link in links or []:
            if isinstance(link, NavLink | NavDropdown):
                self.links.append(link)
            else:
                self.links.append(NavLink(**link))

    # ---------- rendering helpers ----------
    def _wrap_li(self, inner_html) -> Markup:
        return Markup('<li class="{cls}">{inner}</li>').format(cls=NAV_ITEM_CLASS, inner=inner_html)

    # ---------- main links (replaces nav_link / nav_link_with_args) ----------
    def render_main_links(self, is_admin=False) -> Markup:
        parts = []

        for link in self.links:
            if link.disabled:
                continue

            if link.for_admin and not is_admin:
                continue

            if isinstance(link, NavDropdown):
                markup = link.render()
            else:
                markup = self._wrap_li(link.render())
            if markup:
                parts.append(markup)

        return Markup("").join(parts)

    # ---------- user links (profile / logout / login) ----------
    def render_user_links(self, profile_url: str, current_username=None) -> Markup:
        parts = []
        if current_username:
            active = bool(request and quote(request.path) == profile_url)
            logger.debug(f"render_user_links: {profile_url=} {request.path=}")
            active_class = " active" if active else ""

            profile_html = Markup(
                '<a class="nav-link d-inline-block me-3{active_class}" href="{url}">'
                '<i class="bi bi-person-circle me-1"></i>'
                '<span class="navbar-text">{username}</span>'
                "</a>"
            ).format(active_class=active_class, url=escape(profile_url), username=escape(current_username))

            a_link = """
                <a class="btn btn-outline-secondary btn-sm" href="{url}">
                    Logout
                </a>
            """
            logout_html = Markup(a_link).format(
                url=escape(url_for("auth.logout"))
            )

            parts.append(self._wrap_li(profile_html))
            parts.append(self._wrap_li(logout_html))
        else:
            a_link = """
                <a class="btn btn-outline-success btn-sm" href="{url}">
                    Login
                </a>
            """
            login_html = Markup(a_link).format(
                url=escape(url_for("auth.login"))
            )
            parts.append(self._wrap_li(login_html))

        return Markup("").join(parts)


__all__ = [
    "NavigationBar",
]
