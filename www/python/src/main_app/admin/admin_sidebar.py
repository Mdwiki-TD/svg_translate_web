"""Admin sidebar ."""

from __future__ import annotations

import logging

from ..templates_markups.sidebar import Sidebar, SidebarGroup, SidebarItem

logger = logging.getLogger(__name__)

def _load_admin_tools() -> list[SidebarGroup]:
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
            SidebarItem.dashboard_item(
                "templates",
                "Templates",
                "bi-list-columns",
                "admin_panel.templates.dashboard",
                "/admin_panel/templates/",
            ),
            SidebarItem.dashboard_item(
                "templates_need_update",
                "Templates Need Update",
                "bi-arrow-repeat",
                "admin_panel.templates.templates_need_update",
                "/admin_panel/templates/templates-need-update",
            ),
            SidebarItem.dashboard_item(
                "owid_charts",
                "OWID Charts",
                "bi-graph-up",
                "admin_panel.owidcharts.dashboard",
                "/admin_panel/owidcharts/",
            ),
            SidebarItem.dashboard_item(
                "slug_redirects",
                "Slug Redirects",
                "bi-arrow-right-circle",
                "admin_panel.slugredirects.dashboard",
                "/admin_panel/slugredirects/",
            ),
        ],
    )

    users_group = SidebarGroup(
        id="users",
        title="Users",
        icon="bi-person",
        items=[
            SidebarItem.dashboard_item(
                "admins",
                "Admins",
                "bi-person-gear",
                "admin_panel.admins.dashboard",
                "/admin_panel/admins/",
            ),
            SidebarItem.dashboard_item(
                "users",
                "Users",
                "bi-person",
                "admin_panel.users.dashboard",
                "/admin_panel/users/",
            ),
        ],
    )

    db_jobs = SidebarGroup(
        id="db_jobs",
        title="DB Jobs",
        icon="bi-database-fill",
        items=[
            SidebarItem.from_job_item(
                "collect_templates_data",
                "Collect Templates data",
                "bi-kanban",
            ),
            SidebarItem.from_job_item(
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
            SidebarItem.from_job_item("crop_main_files", "Crop Newest World Files", "bi-crop"),
            SidebarItem.from_job_item("fix_nested_main_files", "Fix Nested Main Files", "bi-tools"),
            SidebarItem.from_job_item("update_wikitext", "Update Files Wikitext", "bi-file-earmark-text"),
            SidebarItem.from_job_item(
                "download_main_files",
                "Download Main Files",
                "bi-download",
                disabled=True,
            ),
        ],
    )

    owid_temp_pages = SidebarGroup(
        id="owid_temp_pages",
        title="OWID Templates/Pages",
        icon="bi-file-earmark-richtext",
        items=[
            SidebarItem.from_job_item("create_owid_pages", "Create OWID Pages", "bi-file-earmark-text"),
            SidebarItem.from_job_item("rename_owid_pages", "Rename OWID Pages", "bi-fonts"),
            SidebarItem.from_job_item(
                "add_svglanguages_template",
                "Add {{SVGLanguages}}",
                "bi-file-earmark-text",
            ),
            SidebarItem.from_job_item("add_lang_categories_to_owid_pages", "Add Lang Categories", "bi-tags"),
        ],
    )

    settings_group = SidebarGroup(
        id="settings",
        title="Settings",
        icon="bi-sliders",
        items=[
            SidebarItem.dashboard_item(
                "settings",
                "Settings",
                "bi-gear",
                "admin_panel.settings.dashboard",
                "/admin_panel/settings/",
            ),
            SidebarItem(
                id="db_admin",
                requires_admin=True,
                fallback_href="/admin_panel/db_admin",
                title="DB admin",
                icon="bi-database",
            ),
            SidebarItem.dashboard_item(
                "errors",
                "App Errors",
                "bi-exclamation-triangle",
                "admin_panel.errors.dashboard",
                "/admin_panel/errors/",
            ),
            SidebarItem(
                id="error_logs",
                requires_admin=True,
                fallback_href="/admin_panel/error-logs",
                title="Request Errors logs",
                icon="bi-exclamation-triangle",
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


def create_admin_sidebar(
    path: str,
    is_admin: bool = False,
    list_items: list[SidebarGroup] | None = None,
) -> str:
    """
    Generate sidebar HTML structure based on menu definitions.

    This is the public entry point used by the Jinja template.
    """
    main_menu = list_items or _load_admin_tools()
    sidebar = Sidebar(main_menu)
    return sidebar.render(path, is_admin=is_admin)


__all__ = [
    "create_admin_sidebar",
]
