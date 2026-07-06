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


def job_list_url(job_type: str) -> str:
    return _safe_url_for("admin.jobs.jobs_list", f"/admin/jobs/{job_type}", job_type=job_type)


@functools.lru_cache(maxsize=1)
def load_menu() -> dict[str, list[SidebarItem]]:
    main_menu = {
        "Main": [
            SidebarItem(
                id="templates",
                admin=1,
                href=_safe_url_for("admin.templates.dashboard", "/admin/templates/"),
                title="Templates",
                icon="bi-list-columns",
            ),
            SidebarItem(
                id="templates_need_update",
                admin=1,
                href=_safe_url_for("admin.templates.templates_need_update", "/admin/templates/templates-need-update"),
                title="Templates Need Update",
                icon="bi-arrow-repeat",
            ),
            SidebarItem(
                id="owid_charts",
                admin=1,
                href=_safe_url_for("admin.owidcharts.dashboard", "/admin/owidcharts/"),
                title="OWID Charts",
                icon="bi-graph-up",
            ),
            SidebarItem(
                id="slug_redirects",
                admin=1,
                href=_safe_url_for("admin.slugredirects.dashboard", "/admin/slugredirects/"),
                title="Slug Redirects",
                icon="bi-arrow-right-circle",
            ),
        ],
        "Users": [
            SidebarItem(
                id="admins",
                admin=1,
                href=_safe_url_for("admin.coordinators.dashboard", "/admin/coordinators/"),
                title="Coordinators",
                icon="bi-person-gear",
            ),
            SidebarItem(
                id="users",
                admin=1,
                href=_safe_url_for("admin.users.dashboard", "/admin/users/"),
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
                href=_safe_url_for("admin.settings.dashboard", "/admin/settings/"),
                title="Settings",
                icon="bi-gear",
            ),
        ],
    }
    return main_menu


def _safe_url_for(endpoint: str, fallback: str, **values) -> str:
    if has_request_context():
        return url_for(endpoint, **values)
    return fallback


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

    def get_the_active_group_and_sub(self) -> tuple[str, int]:
        active_group = ""
        active_id = 0

        for key, items in self.menu.items():
            css_class_full = [item.href for item in items if self.path == item.href]
            for item in items:
                css_class = "active" if item.href in css_class_full else ""
                if css_class:
                    active_id = item.id
                    active_group = key
                    break

                elif not css_class_full:
                    if self.path == item.href or (self.path and self.path.startswith(item.href)):
                        css_class = "active"

                    if not css_class and self.active_route == item.id:
                        css_class = "active"

                if css_class:
                    active_group = key
                    active_id = item.id
                    break

        if not active_group:
            active_group = list(self.menu.keys())[0]

        return active_group, active_id

    def create_side(self) -> str:
        """Generate sidebar HTML structure based on menu definitions."""
        sidebar = ["<ul class='list-unstyled'>"]

        # logger.debug(f"Generating sidebar for active_route='{active_route}'")

        active_group, active_id = self.get_the_active_group_and_sub()

        for group, items in self.menu.items():
            sub_items: list[Any] = []
            group_id = group.lower().replace(" ", "_")
            for item in items:
                if item.disabled:
                    continue

                css_class = "active" if item.id == active_id else ""

                link = generate_list_item(item)

                sub_items.append(f"<li id='{item.id}' class='{css_class}'>{link}</li>")

            if sub_items:
                show = "show" if group == active_group else ""
                expanded = "true" if group == active_group else "false"
                icon = self.menu_icons.get(group, "")
                icon_tag = f"<i class='bi {icon} me-1'></i>" if icon else ""

                group_html = f"""
                    <li class="mb-1">
                        <button class="btn btn-toggle align-items-center rounded"
                                data-bs-toggle="collapse"
                                data-bs-target="#{group_id}-collapse"
                                aria-expanded="{expanded}">
                            {icon_tag}
                            <span class='hide-on-collapse-inline'>{group}</span>
                        </button>
                        <div class="collapse {show}" id="{group_id}-collapse">
                            <div class="d-none d-md-inline">
                                <!-- desktop -->
                                <ul class="btn-toggle-nav list-unstyled fw-normal pb-1 small">
                                    {"".join(sub_items)}
                                </ul>
                            </div>
                            <div class="d-inline d-md-none">
                                <!-- mobile -->
                                <ul class="navbar-nav flex-row flex-wrap btn-toggle-nav-mobile list-unstyled fw-normal pb-1 small">
                                    {"".join(sub_items)}
                                </ul>
                            </div>
                        </div>
                    </li>
                    <li class="border-top my-1"></li>
                """
                sidebar.append(group_html.strip())

        sidebar.append("</ul>")
        return "\n".join(sidebar)


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
