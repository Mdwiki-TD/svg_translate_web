"""Unit tests for src/main_app/templates_markups/admin_sidebar.py."""

from __future__ import annotations

from src.main_app.templates_markups.admin_sidebar import (
    SidebarItem,
    create_side,
    generate_list_item,
)


class TestSidebarItem:
    def test_create(self):
        item = SidebarItem(id="test", title="Test", fallback_href="/test", requires_admin=False)
        assert item.id == "test"
        assert item.requires_admin is False
        assert item.fallback_href == "/test"
        assert item.title == "Test"
        assert item.icon is None
        assert item.link_target is None
        assert item.disabled is False

    def test_with_icon(self):
        item = SidebarItem(id="x", title="X", fallback_href="/x", icon="bi-gear")
        assert item.icon == "bi-gear"

    def test_requires_admin_defaults_to_true(self):
        item = SidebarItem(id="x", title="X", fallback_href="/x")
        assert item.requires_admin is True

    def test_resolve_href_uses_fallback_without_endpoint(self):
        item = SidebarItem(id="x", title="X", fallback_href="/x")
        assert item.resolve_href() == "/x"

    def test_resolve_href_uses_endpoint_within_request_context(self, mock_app):
        mock_app.add_url_rule("/adminpanel/settings/", endpoint="adminpanel.settings.dashboard")
        item = SidebarItem(
            id="settings",
            title="Settings",
            endpoint="adminpanel.settings.dashboard",
            fallback_href="/adminpanel/settings/",
        )
        with mock_app.test_request_context():
            assert item.resolve_href() == "/adminpanel/settings/"

    def test_resolve_href_falls_back_on_missing_endpoint(self, mock_app):
        item = SidebarItem(
            id="missing",
            title="Missing",
            endpoint="does.not.exist",
            fallback_href="/adminpanel/missing",
        )
        with mock_app.test_request_context():
            assert item.resolve_href() == "/adminpanel/missing"

    def test_resolve_href_uses_fallback_outside_request_context(self):
        item = SidebarItem(
            id="settings",
            title="Settings",
            endpoint="adminpanel.settings.dashboard",
            fallback_href="/adminpanel/settings/",
        )
        assert item.resolve_href() == "/adminpanel/settings/"


class TestGenerateListItem:
    def test_basic_link(self):
        item = SidebarItem(
            id="test", fallback_href="/test", title="Test Page", icon=None, link_target=None, disabled=False
        )
        html = generate_list_item(item)
        assert "/test" in html
        assert "Test Page" in html
        assert "<a" in html

    def test_with_icon(self):
        item = SidebarItem(
            id="test", fallback_href="/test", title="Test", icon="bi-gear", link_target=None, disabled=False
        )
        html = generate_list_item(item)
        assert "bi-gear" in html

    def test_with_target_blank(self):
        item = SidebarItem(
            id="test", fallback_href="/test", title="Test", icon="bi-gear", link_target="_blank", disabled=False
        )
        html = generate_list_item(item)
        assert "target='_blank'" in html

    def test_with_target_blank_has_noopener_rel(self):
        item = SidebarItem(
            id="test", fallback_href="/test", title="Test", icon="bi-gear", link_target="_blank", disabled=False
        )
        html = generate_list_item(item)
        assert "rel='noopener noreferrer'" in html

    def test_no_target_by_default(self):
        item = SidebarItem(
            id="test", fallback_href="/test", title="Test", icon=None, link_target=None, disabled=False
        )
        html = generate_list_item(item)
        assert "target=" not in html

    def test_generate_list_item(self) -> None:
        item = SidebarItem(
            id="home", fallback_href="/home", title="Home", icon="bi-house", link_target="_blank", disabled=False
        )
        html = generate_list_item(item)
        assert "/home" in html
        assert "bi-house" in html
        assert "target='_blank'" in html
        assert "Home" in html

    def test_generate_list_item_basic(self) -> None:
        item = SidebarItem(
            id="home", fallback_href="/adminpanel/home", title="Home", icon=None, link_target=None, disabled=False
        )
        result = generate_list_item(item)
        assert "/adminpanel/home" in result
        assert "title='Home'" in result
        assert "<i class" not in result
        assert "target=" not in result
        assert "<span class='hide-on-collapse-inline'>Home</span>" in result

    def test_generate_list_item_with_icon(self) -> None:
        item = SidebarItem(
            id="home",
            fallback_href="/adminpanel/home",
            title="Home",
            icon="bi-house",
            link_target=None,
            disabled=False,
        )
        result = generate_list_item(item)
        assert "/adminpanel/home" in result
        assert "title='Home'" in result
        assert "<i class='bi bi-house me-1'></i>" in result
        assert "target=" not in result
        assert "<span class='hide-on-collapse-inline'>Home</span>" in result

    def test_generate_list_item_with_target(self) -> None:
        item = SidebarItem(
            id="home", fallback_href="/home", title="Home", icon=None, link_target="_blank", disabled=False
        )
        result = generate_list_item(item)
        assert "/home" in result
        assert "title='Home'" in result
        assert "<i class" not in result
        assert "target='_blank'" in result
        assert "<span class='hide-on-collapse-inline'>Home</span>" in result

    def test_generate_list_item_with_icon_and_target(self) -> None:
        item = SidebarItem(
            id="home", fallback_href="/home", title="Home", icon="bi-house", link_target="_blank", disabled=False
        )
        result = generate_list_item(item)
        assert "/home" in result
        assert "title='Home'" in result
        assert "<i class='bi bi-house me-1'></i>" in result
        assert "target='_blank'" in result
        assert "<span class='hide-on-collapse-inline'>Home</span>" in result


class TestCreateSide:
    def test_returns_html_string(self, mock_app):
        with mock_app.test_request_context():
            html = create_side("admins", is_admin=True)
            assert isinstance(html, str)
            assert "<ul" in html

    def test_contains_coordinators_link(self, mock_app):
        with mock_app.test_request_context():
            html = create_side("admins", is_admin=True)
            assert "Coordinators" in html

    def test_contains_users_link(self, mock_app):
        with mock_app.test_request_context():
            html = create_side("admins", is_admin=True)
            assert "Users" in html

    def test_create_side_marks_active_item(self) -> None:
        html = create_side("/adminpanel/templates/", is_admin=True)

        assert "Coordinators" in html
        assert "active" in html
        assert html.count("<ul") >= 2

    def test_create_side_with_active_item(self) -> None:
        """
        Tests sidebar creation with an active item.
        """
        result = create_side("admins", is_admin=True)
        assert 'aria-expanded="true"' in result
        assert 'class="collapse show"' in result

    def test_sidebar_contains_jobs_section(self) -> None:
        """Test that sidebar contains the Jobs section."""
        result = create_side("collect_templates_data", is_admin=True)
        assert "DB Jobs" in result
        assert "Files Jobs" in result
        assert "OWID Templates/Pages" in result
        assert "bi-database-fill" in result
        assert "bi-files" in result
        assert "bi-file-earmark-richtext" in result

    def test_sidebar_contains_collect_templates_data_job_link(self) -> None:
        """Test that sidebar contains Collect Templates data job link."""
        result = create_side("collect_templates_data", is_admin=True)
        assert "Collect Templates data" in result
        assert "/adminpanel/jobs/collect_templates_data" in result
        assert "bi-kanban" in result

    def test_sidebar_contains_fix_nested_main_files_job_link(self) -> None:
        """Test that sidebar contains Fix Nested Main Files job link."""
        result = create_side("fix_nested_main_files", is_admin=True)
        assert "Fix Nested Main Files" in result
        assert "/adminpanel/jobs/fix_nested_main_files" in result
        assert "bi-tools" in result

    def test_sidebar_marks_collect_templates_data_as_active(self) -> None:
        """Test that Collect Templates data is marked as active when selected."""
        result = create_side("/adminpanel/jobs/collect_templates_data", is_admin=True)
        # The link should have an active class
        assert "id='collect_templates_data' class='active'" in result

    def test_sidebar_marks_fix_nested_main_files_as_active(self) -> None:
        """Test that Fix Nested Main Files is marked as active when selected."""
        result = create_side("/adminpanel/jobs/fix_nested_main_files", is_admin=True)
        # The link should have an active class
        assert "id='fix_nested_main_files' class='active'" in result


class TestCreateSideIsAdmin:
    """Tests for the new `is_admin` filtering behavior."""

    def test_admin_items_visible_by_default(self) -> None:
        result = create_side("/adminpanel/templates/", is_admin=True)
        assert "Templates" in result

    def test_admin_items_hidden_for_non_admin(self) -> None:
        result = create_side("/adminpanel/templates/", is_admin=False)
        assert "Templates" not in result

    def test_non_admin_still_returns_valid_shell(self) -> None:
        result = create_side("/adminpanel/templates/", is_admin=False)
        assert isinstance(result, str)
        assert "<ul" in result
