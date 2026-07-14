from __future__ import annotations

import functools
import logging
from dataclasses import dataclass
from typing import Any

from flask import has_request_context, url_for

logger = logging.getLogger(__name__)


@dataclass
class SidebarGroup:
    """Sidebar group item definition."""

    id: str
    title: str
    icon: str | None = None
    items: list[SidebarItem] | None = None


@dataclass
class SidebarItem:
    """Sidebar menu item definition."""

    id: str
    admin: int
    href: str
    title: str
    icon: str | None = None
    target: str | None = None
    disabled: bool = False


def _safe_url_for(endpoint: str, fallback: str, **values) -> str:
    if has_request_context():
        return url_for(endpoint, **values)
    return fallback


def job_list_url(job_type: str) -> str:
    return _safe_url_for("adminpanel.jobs.jobs_list", f"/adminpanel/jobs/{job_type}", job_type=job_type)


def generate_list_item(item: SidebarItem) -> str:
    """Generate HTML for a single navigation link."""
    href_full = item.href if item.target else f"/adminpanel/{item.href}"
    if item.href.startswith("/adminpanel/"):
        href_full = item.href

    icon_tag = f"<i class='bi {item.icon} me-1'></i>" if item.icon else ""
    target_attr = "target='_blank'" if item.target else ""
    link = f"""
        <a {target_attr} class='link_nav rounded' href='{href_full}' title='{item.title}'
           data-bs-toggle='tooltip' data-bs-placement='right'>
            {icon_tag}
            <span class='hide-on-collapse-inline'>{item.title}</span>
        </a>
    """
    return link.strip()


class Sidebar:
    def __init__(
        self,
        menu: list[SidebarGroup],
        active_route: str,
        path: str | None = None,
    ) -> None:
        self.menu = menu
        self.active_route = active_route
        self.path = path

    def get_the_active_group_and_sub(self) -> tuple[str, str]:
        """
        Determines the active menu group and the active menu item ID based on the current path or active route.

        This method iterates through the menu items to find an exact match for the current path.
        If an exact match is found, it immediately sets the corresponding group and item ID as active.
        If no exact match is found, it falls back to checking if the current path starts with an item's href,
        or if an item's ID matches the active_route attribute.
        If no active group is determined after checking all items, it defaults to the first group in the menu.

        Returns:
            tuple[str, str]: The active group key and the active item ID.
        """
        # First pass: look for an exact match across all groups
        for group in self.menu:
            for item in group.items:
                if self.path == item.href:
                    return group.title, item.id

        # Second pass: fallback match (startswith or active_route)
        for group in self.menu:
            for item in group.items:
                if (self.path and item.href and self.path.startswith(item.href)) or self.active_route == item.id:
                    return group.title, item.id

        # Default to the first group if no match is found
        active_group = [x.title for x in self.menu][0] if self.menu else ""
        return active_group, ""

    def create_side(self) -> str:
        """Generate sidebar HTML structure based on menu definitions.

        This method constructs a responsive sidebar with collapsible groups and
        sub-items. It determines the active menu item to highlight it and expand
        its parent group. The generated HTML includes separate structures for
        desktop and mobile views using Bootstrap utility classes.

        Returns:
            str: A string containing the formatted HTML structure of the sidebar.
        """

        # Helper lambda to generate sub-items HTML string using a comprehension
        def build_sub_items(items, active_id) -> str:
            sub_items: list[Any] = []

            for item in items:
                if item.disabled:
                    continue

                css_class = "active" if item.id == active_id else ""

                link = generate_list_item(item)

                sub_items.append(f"<li id='{item.id}' class='{css_class}'>{link}</li>")

            sub_items_str = "".join(sub_items)
            return sub_items_str

        active_group, active_id = self.get_the_active_group_and_sub()

        # Template for the collapsible content (shared by desktop and mobile)
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

            match group_obj.title == active_group:
                case True:
                    show, expanded = "show", "true"
                case False:
                    show, expanded = "", "false"

            icon_tag = f"<i class='bi {group_obj.icon} me-1'></i>" if group_obj.icon else ""

            # Formatting the button and the collapse container
            button_html = f"""
                <button class="btn btn-toggle align-items-center rounded"
                        data-bs-toggle="collapse"
                        data-bs-target="#{group_obj.id}-collapse"
                        aria-expanded="{expanded}">
                    {icon_tag}
                    <span class='hide-on-collapse-inline'>{group_obj.title}</span>
                </button>
            """

            group_container = f"""
                <li class="mb-1">
                    {button_html}
                    {collapse_tpl.format(show=show, group_id=group_obj.id, sub_items=sub_items_str)}
                </li>
                <li class="border-top my-1"></li>"""

            sidebar_parts.append(group_container.strip())

        sidebar_parts.append("</ul>")
        return "\n".join(sidebar_parts)


@functools.lru_cache(maxsize=1)
def load_groups_menu() -> list[SidebarGroup]:
    main_group = SidebarGroup(
        id="main",
        title="Main",
        icon="bi-file-text",
        items=[
            SidebarItem(
                id="templates",
                admin=1,
                href=_safe_url_for("adminpanel.templates.dashboard", "/adminpanel/templates/"),
                title="Templates",
                icon="bi-list-columns",
            ),
            SidebarItem(
                id="templates_need_update",
                admin=1,
                href=_safe_url_for(
                    "adminpanel.templates.templates_need_update", "/adminpanel/templates/templates-need-update"
                ),
                title="Templates Need Update",
                icon="bi-arrow-repeat",
            ),
            SidebarItem(
                id="owid_charts",
                admin=1,
                href=_safe_url_for("adminpanel.owidcharts.dashboard", "/adminpanel/owidcharts/"),
                title="OWID Charts",
                icon="bi-graph-up",
            ),
            SidebarItem(
                id="slug_redirects",
                admin=1,
                href=_safe_url_for("adminpanel.slugredirects.dashboard", "/adminpanel/slugredirects/"),
                title="Slug Redirects",
                icon="bi-arrow-right-circle",
            ),
        ],
    )

    users_group = SidebarGroup(
        id="users",
        icon="bi-person",
        title="Users",
        items=[
            SidebarItem(
                id="admins",
                admin=1,
                href=_safe_url_for("adminpanel.coordinators.dashboard", "/adminpanel/coordinators/"),
                title="Coordinators",
                icon="bi-person-gear",
            ),
            SidebarItem(
                id="users",
                admin=1,
                href=_safe_url_for("adminpanel.users.dashboard", "/adminpanel/users/"),
                title="Users",
                icon="bi-person",
            ),
        ],
    )

    db_jobs = SidebarGroup(
        id="db_jobs",
        title="DB Jobs",
        icon="bi-database-fill",
        items=[
            SidebarItem(
                id="collect_templates_data",
                admin=1,
                href=job_list_url("collect_templates_data"),
                title="Collect Templates data",
                icon="bi-kanban",
            ),
            SidebarItem(
                id="update_owid_charts",
                admin=1,
                href=job_list_url("update_owid_charts"),
                title="Update OWID Charts",
                icon="bi-arrow-repeat",
            ),
        ],
    )

    files_jobs = SidebarGroup(
        id="files_jobs",
        title="Files Jobs",
        icon="bi-files",
        items=[
            SidebarItem(
                id="crop_main_files",
                admin=1,
                href=job_list_url("crop_main_files"),
                title="Crop Newest World Files",
                icon="bi-crop",
            ),
            SidebarItem(
                id="fix_nested_main_files",
                admin=1,
                href=job_list_url("fix_nested_main_files"),
                title="Fix Nested Main Files",
                icon="bi-tools",
            ),
            SidebarItem(
                id="download_main_files",
                admin=1,
                href=job_list_url("download_main_files"),
                title="Download Main Files",
                icon="bi-download",
                disabled=True,
            ),
        ],
    )

    owid_temp_pages = SidebarGroup(
        id="owid_temp_pages",
        title="OWID Templates/Pages",
        icon="bi-file-earmark-richtext",
        items=[
            SidebarItem(
                id="create_owid_pages",
                admin=1,
                href=job_list_url("create_owid_pages"),
                title="Create OWID Pages",
                icon="bi-file-earmark-text",
            ),
            SidebarItem(
                id="rename_owid_pages",
                admin=1,
                href=job_list_url("rename_owid_pages"),
                title="Rename OWID Pages",
                icon="bi-fonts",
            ),
            SidebarItem(
                id="add_svglanguages_template",
                admin=1,
                href=job_list_url("add_svglanguages_template"),
                title="Add {{SVGLanguages}}",
                icon="bi-file-earmark-text",
            ),
        ],
    )

    settings_group = SidebarGroup(
        id="settings",
        title="Settings",
        icon="bi-sliders",
        items=[
            SidebarItem(
                id="settings",
                admin=1,
                href=_safe_url_for("adminpanel.settings.dashboard", "/adminpanel/settings/"),
                title="Settings",
                icon="bi-gear",
            ),
        ],
    )

    new_menu = [
        main_group,
        users_group,
        db_jobs,
        files_jobs,
        owid_temp_pages,
        settings_group,
    ]

    return new_menu


def create_side(active_route: str, path: str | None = None) -> str:
    """Generate sidebar HTML structure based on menu definitions."""
    main_menu = load_groups_menu()

    model = Sidebar(main_menu, active_route, path)
    sidebar = model.create_side()

    return sidebar


__all__ = [
    "SidebarItem",
    "generate_list_item",
    "create_side",
]
