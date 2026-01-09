

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


def create_side(ty):
    """Generate sidebar HTML structure based on menu definitions."""
    main_menu_icons = {
        "Translations": "bi-translate",
        "Tasks": "bi-file-text",
        "Fix Nested Tasks": "bi-database",
        "Others": "bi-three-dots",
        "Tools": "bi-tools",
        "Jobs": "bi-gear-fill",
    }

    main_menu = {
        "Tasks": [
            {
                "id": "last", "admin": 0, "href": "recent",
                "title": "Recent", "icon": "bi-clock-history"
            },
            {
                "id": "admins", "admin": 1, "href": "coordinators",
                "title": "Coordinators", "icon": "bi-person-gear"
            },
            {
                "id": "templates", "admin": 1, "href": "templates",
                "title": "Templates", "icon": "bi-list-columns"
            },
        ],
        "Jobs": [
            {
                "id": "collect_main_files_jobs", "admin": 1,
                "href": "collect-main-files",
                "title": "Collect Main Files", "icon": "bi-kanban"
            },
            {
                "id": "fix_nested_main_files_jobs", "admin": 1,
                "href": "fix-nested-main-files",
                "title": "Fix Nested Main Files", "icon": "bi-tools"
            },
        ],
    }

    sidebar = ["<ul class='list-unstyled'>"]

    for key, items in main_menu.items():
        lis = []
        group_is_active = True
        key_id = key.lower().replace(" ", "_")
        for item in items:
            href = item.get("href", "")
            # group_is_active = href == ty

            icon_1 = item.get("icon")
            target = item.get("target")
            css_class = "active" if ty == href else ""
            href_full = href if target else f"/admin/{href}"
            link = generate_list_item(href_full, item["title"], icon_1, target)
            lis.append(f"<li id='{item['id']}' class='{css_class}'>{link}</li>")

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
                                {''.join(lis)}
                            </ul>
                        </div>
                        <div class="d-inline d-md-none">
                            <!-- mobile -->
                            <ul class="navbar-nav flex-row flex-wrap btn-toggle-nav-mobile list-unstyled fw-normal pb-1 small">
                                {''.join(lis)}
                            </ul>
                        </div>
                    </div>
                </li>
                <li class="border-top my-1"></li>
            """
            sidebar.append(group_html.strip())

    sidebar.append("</ul>")
    return "\n".join(sidebar)
