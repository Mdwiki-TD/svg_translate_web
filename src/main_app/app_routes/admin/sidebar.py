from __future__ import annotations

import logging
from dataclasses import dataclass

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


def generate_list_item(href, title, icon=None, target=None):
    """Generate HTML for a single navigation link."""
    icon_tag = f"<i class='bi {icon} me-1'></i>" if icon else ""
    target_attr = "target='_blank'" if target else ""
    link = f"""
        <a {target_attr} class='link_nav rounded' href='{href}' title='{title}'
           data-bs-toggle='tooltip' data-bs-placement='right'>
            {icon_tag}
            <span class='hide-on-collapse-inline'>{title}</span>
        </a>
    """
    return link.strip()


def create_side(active_route):
    """Generate sidebar HTML structure based on menu definitions."""
    main_menu_icons = {
        "Translations": "bi-translate",
        "Main": "bi-file-text",
        "Fix Nested Tasks": "bi-database",
        "Others": "bi-three-dots",
        "Tools": "bi-tools",
        "Jobs": "bi-gear-fill",
        "Settings": "bi-sliders",
    }

    main_menu = {
        "Main": [
            SidebarItem(
                id="last",
                admin=0,
                href="recent",
                title="Tasks",
                icon="bi-clock-history",
            ),
            SidebarItem(
                id="admins",
                admin=1,
                href="coordinators",
                title="Coordinators",
                icon="bi-person-gear",
            ),
            SidebarItem(
                id="templates",
                admin=1,
                href="templates",
                title="Templates",
                icon="bi-list-columns",
            ),
            SidebarItem(
                id="owid_charts",
                admin=1,
                href="owid-charts",
                title="OWID Charts",
                icon="bi-graph-up",
            ),
        ],
        "Jobs": [
            SidebarItem(
                id="collect_main_files",
                admin=1,
                href="collect_main_files/list",
                title="Collect Templates data",
                icon="bi-kanban",
            ),
            SidebarItem(
                id="crop_main_files",
                admin=1,
                href="crop_main_files/list",
                title="Crop Newest World Files",
                icon="bi-crop",
            ),
            SidebarItem(
                id="create_owid_pages",
                admin=1,
                href="create_owid_pages/list",
                title="Create OWID Pages",
                icon="bi-file-earmark-text",
            ),
            SidebarItem(
                id="add_svglanguages_template",
                admin=1,
                href="add_svglanguages_template/list",
                title="Add {{SVGLanguages}}",
                icon="bi-file-earmark-text",
            ),
            SidebarItem(
                id="fix_nested_main_files",
                admin=1,
                href="fix_nested_main_files/list",
                title="Fix Nested Main Files",
                icon="bi-tools",
            ),
            SidebarItem(
                id="download_main_files",
                admin=1,
                href="download_main_files/list",
                title="Download Main Files",
                icon="bi-download",
                disabled=True,
            ),
        ],
        "Settings": [
            SidebarItem(
                id="settings",
                admin=1,
                href="settings",
                title="Settings",
                icon="bi-gear",
            ),
        ],
    }

    sidebar = ["<ul class='list-unstyled'>"]

    # logger.debug(f"Generating sidebar for active_route='{active_route}'")

    for key, items in main_menu.items():
        lis = []
        group_is_active = True
        key_id = key.lower().replace(" ", "_")
        for item in items:
            if item.disabled:
                continue

            css_class = "active" if (active_route == item.href or item.href.startswith(f"{active_route}/")) else ""
            href_full = item.href if item.target else f"/admin/{item.href}"
            link = generate_list_item(href_full, item.title, item.icon, item.target)
            lis.append(f"<li id='{item.id}' class='{css_class}'>{link}</li>")

        if lis:
            show = "show" if group_is_active else ""
            expanded = "true" if group_is_active else "false"
            icon = main_menu_icons.get(key, "")
            icon_tag = f"<i class='bi {icon} me-1'></i>" if icon else ""

            group_html = f"""
                <li class="mb-1">
                    <button class="btn btn-toggle align-items-center rounded"
                            data-bs-toggle="collapse"
                            data-bs-target="#{key_id}-collapse"
                            aria-expanded="{expanded}">
                        {icon_tag}
                        <span class='hide-on-collapse-inline'>{key}</span>
                    </button>
                    <div class="collapse {show}" id="{key_id}-collapse">
                        <div class="d-none d-md-inline">
                            <!-- desktop -->
                            <ul class="btn-toggle-nav list-unstyled fw-normal pb-1 small">
                                {"".join(lis)}
                            </ul>
                        </div>
                        <div class="d-inline d-md-none">
                            <!-- mobile -->
                            <ul class="navbar-nav flex-row flex-wrap btn-toggle-nav-mobile list-unstyled fw-normal pb-1 small">
                                {"".join(lis)}
                            </ul>
                        </div>
                    </div>
                </li>
                <li class="border-top my-1"></li>
            """
            sidebar.append(group_html.strip())

    sidebar.append("</ul>")
    return "\n".join(sidebar)
