"""
navbar.py
---------
A Navbar object that auto-generates the navigation bar HTML, replacing
the manual Jinja macros (nav_link and nav_link_with_args) that used to
live in navbar.html.

Usage in the template after registering via init_app(app):

    {{ navbar.render_main_links(is_admin=is_admin) }}
    {{ navbar.render_user_links(current_username=current_username) }}

Both methods return a safe Markup object (no need for the |safe filter,
though adding it doesn't hurt).
"""

from dataclasses import dataclass, field

from flask import request, url_for
from markupsafe import Markup, escape


@dataclass
class NavLink:
    """
    Represents a single navigation link.
    """

    text: str
    icon: str
    path: str

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


class Navbar:
    NAV_ITEM_CLASS = "nav-item col-lg-auto col-md-4 col-sm-6 col-6"

    def __init__(self, links=None):
        # A single ordered list of NavLink instances (or dicts) holds both
        # regular and admin-only links; order in this list is render order.
        self.links = []
        for link in links or []:
            self.links.append(link if isinstance(link, NavLink) else NavLink(**link))

    # ---------- rendering helpers ----------
    def _wrap_li(self, inner_html) -> Markup:
        return Markup('<li class="{cls}">{inner}</li>').format(cls=self.NAV_ITEM_CLASS, inner=inner_html)

    # ---------- main links (replaces nav_link / nav_link_with_args) ----------
    def render_main_links(self, is_admin=False) -> Markup:
        parts = []

        for link in self.links:
            if link.for_admin and not is_admin:
                continue
            parts.append(self._wrap_li(link.render()))

        return Markup("").join(parts)

    # ---------- user links (profile / logout / login) ----------
    def render_user_links(self, current_username=None) -> Markup:
        parts = []
        if current_username:
            profile_url = url_for("profile.dashboard", user_name=current_username)
            active = bool(request and request.path == profile_url)
            active_class = " active" if active else ""

            profile_html = Markup(
                '<a class="nav-link d-inline-block me-3{active_class}" href="{url}">'
                '<i class="bi bi-person-circle me-1"></i>'
                '<span class="navbar-text">{username}</span>'
                "</a>"
            ).format(active_class=active_class, url=escape(profile_url), username=escape(current_username))

            logout_html = Markup('<a class="btn btn-outline-secondary btn-sm" href="{url}">Logout</a>').format(
                url=escape(url_for("auth.logout"))
            )

            parts.append(self._wrap_li(profile_html))
            parts.append(self._wrap_li(logout_html))
        else:
            login_html = Markup('<a class="btn btn-outline-success btn-sm" href="{url}">Login</a>').format(
                url=escape(url_for("auth.login"))
            )
            parts.append(self._wrap_li(login_html))

        return Markup("").join(parts)


nav_list = [
    NavLink(
        text="Main Tasks",
        icon="bi-list-task",
        url_endpoint="public_jobs.jobs_list",
        url_kwargs={"job_type": "copy_svg_langs"},
        title="Main Tasks",
        path="/jobs/copy_svg_langs",
    ),
    NavLink(
        text="Fix Nested Tags",
        icon="bi-list-task",
        url_endpoint="public_jobs.jobs_list",
        url_kwargs={"job_type": "fix_nested_jobs"},
        title="Fix Nested Tags",
        path="/jobs/fix_nested_jobs",
    ),
    NavLink(
        text="Admins",
        icon="bi-people-fill",
        url_endpoint="adminpanel.admin_dashboard",
        path="/adminpanel",
        for_admin=True,
    ),
    NavLink(
        text="GitHub",
        icon="bi-github",
        static_url="https://github.com/MrIbrahem/himo_repo",
        link_target="_blank",
        path="",
    ),
]

navbar = Navbar(nav_list)

__all__ = [
    "navbar",
]
