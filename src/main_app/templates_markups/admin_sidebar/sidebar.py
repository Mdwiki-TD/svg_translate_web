"""
<div class="div_menu navbar-collapse">
    {% if create_side %}
    {{ create_side(request.path, is_admin) | safe }}
    {% endif %}
</div>
"""

from __future__ import annotations

import logging

from markupsafe import Markup, escape

from .objects import SidebarGroup, SidebarItem
from .sidebar_list import load_groups_menu

logger = logging.getLogger(__name__)


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
