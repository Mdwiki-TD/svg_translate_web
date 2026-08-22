"""
<div class="div_menu navbar-collapse">
    {% if create_side %}
    {{ create_side(request.path, is_admin) | safe }}
    {% endif %}
</div>
"""

from __future__ import annotations

import functools
import logging
from dataclasses import dataclass, field

from flask import has_request_context, url_for
from markupsafe import Markup, escape
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


def generate_list_item(item: SidebarItem) -> Markup:
    """Generate HTML for a single sidebar navigation link."""
    is_external = bool(item.link_target)
    href = item.resolve_href()

    icon_tag = Markup("<i class='bi {icon} me-1'></i>").format(icon=escape(item.icon)) if item.icon else Markup("")
    target_attr = (
        Markup(" target='{target}' rel='noopener noreferrer'").format(target=escape(item.link_target))
        if is_external
        else Markup("")
    )

    return Markup(
        "<a{target} class='link_nav rounded' href='{href}' title='{title}'"
        " data-bs-toggle='tooltip' data-bs-placement='right'>"
        "{icon}"
        "<span class='hide-on-collapse-inline'>{title}</span>"
        "</a>"
    ).format(
        target=target_attr,
        href=escape(href),
        title=escape(item.title),
        icon=icon_tag,
    )


class Sidebar:
    def __init__(self, menu: list[SidebarGroup]) -> None:
        self.menu = menu

    def get_the_active_group_and_sub(self, active_route: str, path: str) -> tuple[str, str]:
        """
        Determines the active menu group and the active menu item ID based on the current path or active route.

        This method iterates through the menu items to find an exact match for the current path.
        If an exact match is found, it immediately sets the corresponding group and item ID as active.
        If no exact match is found, it falls back to checking if the current path starts with an item's href,
        or if an item's ID matches the active_route attribute.
        If no active group is determined after checking all items, it defaults to the first group in the menu.

        Returns:
            tuple[str, str]: The active group ID and the active item ID.
        """
        # First pass: look for an exact match across all groups
        for group in self.menu:
            for item in group.items:
                if path == item.resolve_href():
                    return group.id, item.id

        # Second pass: fallback match (startswith or active_route)
        for group in self.menu:
            for item in group.items:
                href = item.resolve_href()
                if (path and href and path.startswith(href)) or active_route == item.id:
                    return group.id, item.id

        # Default to the first group if no match is found
        active_group = self.menu[0].id if self.menu else ""
        return active_group, ""

    def render(self, path: str, is_admin: bool = True) -> str:
        """Generate sidebar HTML structure based on menu definitions.

        This method constructs a responsive sidebar with collapsible groups and
        sub-items. It determines the active menu item to highlight it and expand
        its parent group. The generated HTML includes separate structures for
        desktop and mobile views using Bootstrap utility classes.

        Args:
            path: The current request path, used to highlight the active item.
            is_admin: Whether the current user may see admin-only items
                (items with `requires_admin=True`).

        Returns:
            str: A string containing the formatted HTML structure of the sidebar.
        """

        def build_sub_items(items: list[SidebarItem], active_id: str) -> str:
            """Build the <li> HTML for every visible item in a group."""
            sub_items: list[str] = []

            for item in items:
                if item.disabled:
                    continue
                if item.requires_admin and not is_admin:
                    continue

                css_class = "active" if item.id == active_id else ""
                link = generate_list_item(item)

                sub_items.append(f"<li id='{escape(item.id)}' class='{css_class}'>{link}</li>")

            return "".join(sub_items)

        path_parts = path.strip("/").split("/")
        active_route = path_parts[1] if len(path_parts) > 1 else ""

        active_group, active_id = self.get_the_active_group_and_sub(active_route, path)

        # Template for the collapsible content (services by desktop and mobile)
        collapse_tpl = """
            <div class="collapse {show}" id="{group_id}-collapse">
                <div class="d-none d-md-inline">
                    <!-- desktop -->
                    <ul class="btn-toggle-nav list-unstyled fw-normal pb-1 small">
                        {sub_items}
                    </ul>
                </div>
                <div class="d-inline d-md-none">
                    <!-- mobile -->
                    <ul class="navbar-nav flex-row flex-wrap btn-toggle-nav-mobile list-unstyled fw-normal pb-1 small">
                        {sub_items}
                    </ul>
                </div>
            </div>
        """

        sidebar_parts = ["<ul class='list-unstyled'>"]

        for group_obj in self.menu:
            sub_items_str = build_sub_items(group_obj.items, active_id)

            if not sub_items_str:
                continue

            if group_obj.id == active_group:
                show, expanded = "show", "true"
            else:
                show, expanded = "", "false"

            icon_tag = f"<i class='bi {escape(group_obj.icon)} me-1'></i>" if group_obj.icon else ""

            # Formatting the button and the collapse container
            button_html = f"""
                <button class="btn btn-toggle align-items-center rounded"
                        data-bs-toggle="collapse"
                        data-bs-target="#{escape(group_obj.id)}-collapse"
                        aria-expanded="{expanded}">
                    {icon_tag}
                    <span class='hide-on-collapse-inline'>{escape(group_obj.title)}</span>
                </button>
            """

            group_container = f"""
                <li class="mb-1">
                    {button_html}
                    {collapse_tpl.format(show=show, group_id=escape(group_obj.id), sub_items=sub_items_str)}
                </li>
                <li class="border-top my-1"></li>"""

            sidebar_parts.append(group_container.strip())

        sidebar_parts.append("</ul>")
        return "\n".join(sidebar_parts)


# ---------------------------------------------------------------------------
# Menu item builders — small factories to avoid repeating the same
# endpoint/fallback wiring for every dashboard or job-list link.
# ---------------------------------------------------------------------------
def dashboard_item(id_: str, title: str, icon: str, endpoint: str, fallback_href: str) -> SidebarItem:
    """Build a SidebarItem pointing at a regular admin-panel dashboard endpoint."""
    return SidebarItem(id=id_, title=title, icon=icon, endpoint=endpoint, fallback_href=fallback_href)


def job_item(job_type: str, title: str, icon: str, *, disabled: bool = False) -> SidebarItem:
    """Build a SidebarItem pointing at the job-list page for the given job type."""
    return SidebarItem(
        id=job_type,
        title=title,
        icon=icon,
        endpoint="adminpanel.jobs.jobs_list",
        endpoint_kwargs={"job_type": job_type},
        fallback_href=f"/adminpanel/jobs/{job_type}",
        disabled=disabled,
    )


@functools.lru_cache(maxsize=1)
def load_groups_menu() -> list[SidebarGroup]:
    """Build the static sidebar menu structure.

    No Flask request/app context is touched here — URLs are resolved lazily
    by `SidebarItem.resolve_href()` at render time — so this result is safe
    to cache for the lifetime of the process.
    """
    main_group = SidebarGroup(
        id="main",
        title="Main",
        icon="bi-file-text",
        items=[
            dashboard_item(
                "templates",
                "Templates",
                "bi-list-columns",
                "adminpanel.templates.dashboard",
                "/adminpanel/templates/",
            ),
            dashboard_item(
                "templates_need_update",
                "Templates Need Update",
                "bi-arrow-repeat",
                "adminpanel.templates.templates_need_update",
                "/adminpanel/templates/templates-need-update",
            ),
            dashboard_item(
                "owid_charts",
                "OWID Charts",
                "bi-graph-up",
                "adminpanel.owidcharts.dashboard",
                "/adminpanel/owidcharts/",
            ),
            dashboard_item(
                "slug_redirects",
                "Slug Redirects",
                "bi-arrow-right-circle",
                "adminpanel.slugredirects.dashboard",
                "/adminpanel/slugredirects/",
            ),
        ],
    )

    users_group = SidebarGroup(
        id="users",
        title="Users",
        icon="bi-person",
        items=[
            dashboard_item(
                "admins",
                "Coordinators",
                "bi-person-gear",
                "adminpanel.coordinators.dashboard",
                "/adminpanel/coordinators/",
            ),
            dashboard_item(
                "users",
                "Users",
                "bi-person",
                "adminpanel.users.dashboard",
                "/adminpanel/users/",
            ),
        ],
    )

    db_jobs = SidebarGroup(
        id="db_jobs",
        title="DB Jobs",
        icon="bi-database-fill",
        items=[
            job_item(
                "collect_templates_data",
                "Collect Templates data",
                "bi-kanban",
            ),
            job_item(
                "update_owid_charts",
                "Update OWID Charts",
                "bi-arrow-repeat",
            ),
        ],
    )

    files_jobs = SidebarGroup(
        id="files_jobs",
        title="Files Jobs",
        icon="bi-files",
        items=[
            job_item("crop_main_files", "Crop Newest World Files", "bi-crop"),
            job_item("fix_nested_main_files", "Fix Nested Main Files", "bi-tools"),
            job_item("download_main_files", "Download Main Files", "bi-download", disabled=True),
        ],
    )

    owid_temp_pages = SidebarGroup(
        id="owid_temp_pages",
        title="OWID Templates/Pages",
        icon="bi-file-earmark-richtext",
        items=[
            job_item("create_owid_pages", "Create OWID Pages", "bi-file-earmark-text"),
            job_item("rename_owid_pages", "Rename OWID Pages", "bi-fonts"),
            job_item("add_svglanguages_template", "Add {{SVGLanguages}}", "bi-file-earmark-text"),
            job_item("add_lang_categories_to_owid_pages", "Add Lang Categories", "bi-tags"),
        ],
    )

    settings_group = SidebarGroup(
        id="settings",
        title="Settings",
        icon="bi-sliders",
        items=[
            dashboard_item(
                "settings",
                "Settings",
                "bi-gear",
                "adminpanel.settings.dashboard",
                "/adminpanel/settings/",
            ),
            dashboard_item(
                "errors",
                "App Errors",
                "bi-exclamation-triangle",
                "adminpanel.errors.dashboard",
                "/adminpanel/errors/",
            ),
            SidebarItem(
                id="db_admin",
                requires_admin=1,
                fallback_href="/adminpanel/db_admin",
                title="DB admin",
                icon="bi-database",
            ),
        ],
    )

    return [
        main_group,
        users_group,
        db_jobs,
        files_jobs,
        owid_temp_pages,
        settings_group,
    ]


def create_side(path: str, is_admin: bool = False) -> str:
    """
    Generate sidebar HTML structure based on menu definitions.

    This is the public entry point used by the Jinja template.
    """
    main_menu = load_groups_menu()
    sidebar = Sidebar(main_menu)
    return sidebar.render(path, is_admin=is_admin)


__all__ = [
    "create_side",
]
