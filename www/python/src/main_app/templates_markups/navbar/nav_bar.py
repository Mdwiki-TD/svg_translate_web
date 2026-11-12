"""
navbar.py
---------
A Navbar object that auto-generates the navigation bar HTML, replacing
the manual Jinja macros (nav_link and nav_link_with_args) that used to
live in navbar.html.

Usage in the template after registering via init_app(app):

    {{ main_navbar.render_main_links(is_admin) }}
    {{
        main_navbar.render_user_links(current_username)
    }}

Both methods return a safe Markup object (no need for the |safe filter,
though adding it doesn't hurt).
"""

from __future__ import annotations

import logging
from urllib.parse import quote

from flask import request, url_for
from markupsafe import Markup, escape

from .mapping import NAV_ITEM_CLASS, NavDropdown, NavLink

logger = logging.getLogger(__name__)


class NavigationBar:
    def __init__(self, links=None) -> None:
        # A single ordered list holds NavLink and NavDropdown entries
        # (regular, admin-only, or grouped); order in this list is render order.
        self.links: list[NavLink | NavDropdown] = []
        for link in links or []:
            if isinstance(link, NavLink | NavDropdown):
                self.links.append(link)
            else:
                self.links.append(NavLink(**link))

    # ---------- rendering helpers ----------
    def _wrap_li(self, inner_html) -> Markup:
        return Markup('<li class="{cls}">{inner}</li>').format(
            cls=NAV_ITEM_CLASS,
            inner=inner_html,
        )

    def create_collapsible_nav(self) -> Markup:
        return Markup("""
            <div class="d-flex align-items-center order-lg-last">
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
                    aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <button class="btn btn-outline-secondary btn-sm ms-2" id="darkModeToggle" type="button"
                    aria-label="Toggle dark mode">
                    <i class="bi bi-moon-stars-fill"></i>
                </button>
            </div>
        """)

    # ---------- main links (replaces nav_link / nav_link_with_args) ----------
    def render_main_links(self, is_admin=False) -> Markup:
        parts = []

        for link in self.links:
            if link.disabled:
                continue

            if link.for_admins and not is_admin:
                continue

            if isinstance(link, NavDropdown):
                markup = link.render()
            else:
                markup = self._wrap_li(link.render())
            if markup:
                parts.append(markup)

        return Markup("").join(parts)

    # ---------- user links (profile / logout / login) ----------
    def render_user_links(self, current_username: str | None = None) -> Markup:
        parts = []
        if current_username:
            profile_url = url_for("profile.dashboard", user_name=current_username)
            active = bool(request and quote(request.path) == profile_url)
            logger.debug(f"render_user_links: {profile_url=} {request.path=}")
            active_class = " active" if active else ""

            profile_html = Markup(
                '<a class="nav-link d-inline-block me-3{active_class}" href="{url}">'
                '<i class="bi bi-person-circle me-1"></i>'
                '<span class="navbar-text">{username}</span>'
                "</a>"
            ).format(
                active_class=active_class,
                url=escape(profile_url),
                username=escape(current_username),
            )

            a_link = """
                <a class="nav-link py-2 px-0 px-lg-2" href="{url}">
                    <i class="fas fa-sign-out-alt fa-sm fa-fw mr-2"></i>
                    <span class="d-lg-none navtitles">
                        Logout
                    </span>
                </a>
            """
            logout_html = Markup(a_link).format(url=escape(url_for("auth.logout")))

            parts.append(self._wrap_li(profile_html))
            parts.append(self._wrap_li(logout_html))
        else:
            a_link = """
                <a class="nav-link py-2 px-0 px-lg-2" href="{url}">
                    <i class="bi bi-box-arrow-in-right"></i>
                    <span class="navtitles">
                        Login
                    </span>
                </a>
            """
            login_html = Markup(a_link).format(url=escape(url_for("auth.login")))
            parts.append(self._wrap_li(login_html))

        return Markup("").join(parts)

    def render(
        self,
        is_admin=False,
        current_username: str | None = None,
    ) -> Markup:
        main_links = self.render_main_links(is_admin)
        user_links = self.render_user_links(current_username)

        navbar_markup = Markup("""
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto flex-row flex-wrap bd-navbar-nav">
                    {main_links}
                </ul>
                <hr class="d-lg-none text-dark-subtle text-50">
                <ul class="d-flex align-items-center navbar-nav flex-row flex-wrap bd-navbar-nav">
                    {user_links}
                </ul>
            </div>
        """).format(
            main_links=main_links,
            user_links=user_links,
        )
        return navbar_markup


__all__ = [
    "NavigationBar",
]
