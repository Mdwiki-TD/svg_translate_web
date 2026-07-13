from __future__ import annotations

import functools
import logging
from dataclasses import dataclass
from typing import Any

from flask import has_request_context, url_for

logger = logging.getLogger(__name__)


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
    return _safe_url_for("adminpanel.jobs.jobs_list", f"/admin/jobs/{job_type}", job_type=job_type)


def generate_list_item(item: SidebarItem) -> str:
    """Generate HTML for a single navigation link."""
    href_full = item.href if item.target else f"/admin/{item.href}"
    if item.href.startswith("/admin/"):
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
        menu: dict[str, list[SidebarItem]],
        menu_icons: dict[str, str],
        active_route: str,
        path: str | None = None,
    ) -> None:
        self.menu = menu
        self.menu_icons = menu_icons
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
        for key, items in self.menu.items():
            for item in items:
                if self.path == item.href:
                    return key, item.id

        # Second pass: fallback match (startswith or active_route)
        for key, items in self.menu.items():
            for item in items:
                if (self.path and item.href and self.path.startswith(item.href)) or self.active_route == item.id:
                    return key, item.id

        # Default to the first group if no match is found
        active_group = list(self.menu.keys())[0] if self.menu else ""
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

        for group, items in self.menu.items():
            sub_items_str = build_sub_items(items, active_id)

            if not sub_items_str:
                continue

            group_id = group.lower().replace(" ", "_")

            match group == active_group:
                case True:
                    show, expanded = "show", "true"
                case False:
                    show, expanded = "", "false"

            icon = self.menu_icons.get(group, "")
            icon_tag = f"<i class='bi {icon} me-1'></i>" if icon else ""

            # Formatting the button and the collapse container
            button_html = f"""
                <button class="btn btn-toggle align-items-center rounded"
                        data-bs-toggle="collapse"
                        data-bs-target="#{group_id}-collapse"
                        aria-expanded="{expanded}">
                    {icon_tag}
                    <span class='hide-on-collapse-inline'>{group}</span>
                </button>
            """

            group_container = f"""
                <li class="mb-1">
                    {button_html}
                    {collapse_tpl.format(show=show, group_id=group_id, sub_items=sub_items_str)}
                </li>
                <li class="border-top my-1"></li>"""

            sidebar_parts.append(group_container.strip())

        sidebar_parts.append("</ul>")
        return "\n".join(sidebar_parts)


@functools.lru_cache(maxsize=1)
def load_menu() -> dict[str, list[SidebarItem]]:
    main_menu = {
        "Main": [
            SidebarItem(
                id="templates",
                admin=1,
                href=_safe_url_for("adminpanel.templates.dashboard", "/admin/templates/"),
                title="Templates",
                icon="bi-list-columns",
            ),
            SidebarItem(
                id="templates_need_update",
                admin=1,
                href=_safe_url_for(
                    "adminpanel.templates.templates_need_update", "/admin/templates/templates-need-update"
                ),
                title="Templates Need Update",
                icon="bi-arrow-repeat",
            ),
            SidebarItem(
                id="owid_charts",
                admin=1,
                href=_safe_url_for("adminpanel.owidcharts.dashboard", "/admin/owidcharts/"),
                title="OWID Charts",
                icon="bi-graph-up",
            ),
            SidebarItem(
                id="slug_redirects",
                admin=1,
                href=_safe_url_for("adminpanel.slugredirects.dashboard", "/admin/slugredirects/"),
                title="Slug Redirects",
                icon="bi-arrow-right-circle",
            ),
        ],
        "Users": [
            SidebarItem(
                id="admins",
                admin=1,
                href=_safe_url_for("adminpanel.coordinators.dashboard", "/admin/coordinators/"),
                title="Coordinators",
                icon="bi-person-gear",
            ),
            SidebarItem(
                id="users",
                admin=1,
                href=_safe_url_for("adminpanel.users.dashboard", "/admin/users/"),
                title="Users",
                icon="bi-person",
            ),
        ],
        "DB jobs": [
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
        "Files jobs": [
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
        "OWID Templates/Pages": [
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
        "Settings": [
            SidebarItem(
                id="settings",
                admin=1,
                href=_safe_url_for("adminpanel.settings.dashboard", "/admin/settings/"),
                title="Settings",
                icon="bi-gear",
            ),
        ],
    }
    return main_menu


def create_side(active_route: str, path: str | None = None) -> str:
    """Generate sidebar HTML structure based on menu definitions."""
    main_menu = load_menu()

    main_menu_icons = {
        "Translations": "bi-translate",
        "Main": "bi-file-text",
        "Fix Nested Tasks": "bi-database",
        "Others": "bi-three-dots",
        "Tools": "bi-tools",
        "DB jobs": "bi-database-fill",
        "Files jobs": "bi-files",
        "OWID Templates/Pages": "bi-file-earmark-richtext",
        "Settings": "bi-sliders",
        "Users": "bi-person",
    }

    model = Sidebar(main_menu, main_menu_icons, active_route, path)
    sidebar = model.create_side()

    return sidebar


__all__ = [
    "SidebarItem",
    "generate_list_item",
    "create_side",
]
