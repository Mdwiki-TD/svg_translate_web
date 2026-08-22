""" """

from __future__ import annotations

import functools

from .objects import (
    SidebarGroup,
    SidebarItem,
)

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


__all__ = [
    "load_groups_menu",
]
