""" """

from __future__ import annotations

from .objects import NavDropdown, NavLink

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
        text="Templates",
        icon="bi-list-columns",
        url_endpoint="templates.dashboard",
        title="OWID Charts",
        path="/templates",
    ),
    NavLink(
        text="Charts",
        icon="bi-graph-up",
        url_endpoint="owid_charts.all_charts",
        title="OWID Charts",
        path="/owidcharts",
    ),
    NavDropdown(
        text="Extract/Inject",
        icon="bi-filetype-svg",
        dropdown_id="navbarDarkDropdownMenuLink",
        items=[
            NavLink(
                text="Extract",
                icon="bi-file-earmark-text",
                url_endpoint="extract.dashboard",
                path="/extract",
            ),
            NavLink(
                text="Inject",
                icon="bi-arrow-left-right",
                url_endpoint="inject.dashboard",
                path="/inject",
            ),
        ],
    ),
    NavDropdown(
        disabled=True,
        text="Beta",
        icon="bi-filetype-svg",
        dropdown_id="navbarDarkDropdownMenuLink",
        items=[
            NavLink(
                text="Explorer",
                icon="bi-translate",
                url_endpoint="explorer.main",
                path="/Explorer",
            ),
            NavLink(
                text="Translate",
                icon="bi-translate",
                url_endpoint="translate.dashboard",
                path="/translate",
            ),
        ],
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
        static_url="https://github.com/Mdwiki-TD/svg_translate_web",
        link_target="_blank",
        path="",
    ),
]


__all__ = [
    "nav_list",
]
