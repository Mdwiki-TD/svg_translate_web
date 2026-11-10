""" """

from __future__ import annotations

import logging

from .sidebar import Sidebar
from .sidebar_list import load_groups_menu

logger = logging.getLogger(__name__)


def create_admin_sidebar(path: str, is_admin: bool = False) -> str:
    """
    Generate sidebar HTML structure based on menu definitions.

    This is the public entry point used by the Jinja template.
    """
    main_menu = load_groups_menu()
    sidebar = Sidebar(main_menu)
    return sidebar.render(path, is_admin=is_admin)


__all__ = [
    "create_admin_sidebar",
]
