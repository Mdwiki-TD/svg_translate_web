"""Unit tests for src/main_app/app_routes/admin/sidebar.py."""

from __future__ import annotations
from src.main_app.app_routes.admin.sidebar import (
    SidebarItem,
    create_side,
    generate_list_item,
)

class TestSidebarItem:
    def test_create(self):
        item = SidebarItem(id="test", admin=0, href="/test", title="Test")
        assert item.id == "test"
        assert item.admin == 0
        assert item.href == "/test"
        assert item.title == "Test"
        assert item.icon is None
        assert item.target is None
        assert item.disabled is False

    def test_with_icon(self):
        item = SidebarItem(id="x", admin=1, href="/x", title="X", icon="bi-gear")
        assert item.icon == "bi-gear"


class TestGenerateListItem:
    def test_basic_link(self):
        item = SidebarItem(id="test", admin=0, href="/test", title="Test Page", icon=None, target=None, disabled=False)
        html = generate_list_item(item)
        assert "/test" in html
        assert "Test Page" in html
        assert "<a" in html

    def test_with_icon(self):
        item = SidebarItem(id="test", admin=0, href="/test", title="Test", icon="bi-gear", target=None, disabled=False)
        html = generate_list_item(item)
        assert "bi-gear" in html

    def test_with_target_blank(self):
        item = SidebarItem(id="test", admin=0, href="/test", title="Test", icon="bi-gear", target="_blank", disabled=False)
        html = generate_list_item(item)
        assert "target='_blank'" in html

    def test_no_target_by_default(self):
        item = SidebarItem(id="test", admin=0, href="/test", title="Test", icon=None, target=None, disabled=False)
        html = generate_list_item(item)
        assert "target=" not in html

    def test_generate_list_item(self) -> None:
        html = generate_list_item("/home", "Home", icon="bi-house", target=True)
        assert "href='/home'" in html
        assert "bi-house" in html
        assert "target='_blank'" in html
        assert "Home" in html


    def test_generate_list_item_basic(self) -> None:
        """
        Tests basic list item generation.
        """
        result = generate_list_item("/home", "Home")
        assert "href='/home'" in result
        assert "title='Home'" in result
        assert "<i class" not in result
        assert "target=" not in result
        assert "<span class='hide-on-collapse-inline'>Home</span>" in result


    def test_generate_list_item_with_icon(self) -> None:
        """
        Tests list item generation with an icon.
        """
        result = generate_list_item("/home", "Home", icon="bi-house")
        assert "href='/home'" in result
        assert "title='Home'" in result
        assert "<i class='bi bi-house me-1'></i>" in result
        assert "target=" not in result
        assert "<span class='hide-on-collapse-inline'>Home</span>" in result


    def test_generate_list_item_with_target(self) -> None:
        """
        Tests list item generation with a target attribute.
        """
        result = generate_list_item("/home", "Home", target="_blank")
        assert "href='/home'" in result
        assert "title='Home'" in result
        assert "<i class" not in result
        assert "target='_blank'" in result
        assert "<span class='hide-on-collapse-inline'>Home</span>" in result


    def test_generate_list_item_with_icon_and_target(self) -> None:
        """
        Tests list item generation with both an icon and a target attribute.
        """
        result = generate_list_item("/home", "Home", icon="bi-house", target="_blank")
        assert "href='/home'" in result
        assert "title='Home'" in result
        assert "<i class='bi bi-house me-1'></i>" in result
        assert "target='_blank'" in result
        assert "<span class='hide-on-collapse-inline'>Home</span>" in result



class TestCreateSide:
    def test_returns_html_string(self, app):
        with app.test_request_context():
            html = create_side("admins")
            assert isinstance(html, str)
            assert "<ul" in html

    def test_contains_coordinators_link(self, app):
        with app.test_request_context():
            html = create_side("admins")
            assert "Coordinators" in html

    def test_contains_users_link(self, app):
        with app.test_request_context():
            html = create_side("admins")
            assert "Users" in html

    def test_create_side_marks_active_item(self) -> None:
        html = create_side("admins")

        assert "Coordinators" in html
        assert "active" in html
        assert html.count("<ul") >= 2

    def test_create_side_with_active_item(self) -> None:
        """
        Tests sidebar creation with an active item.
        """
        result = create_side("recent")
        assert 'aria-expanded="true"' in result
        assert 'class="collapse show"' in result


    def test_sidebar_contains_jobs_section(self) -> None:
        """Test that sidebar contains the Jobs section."""
        result = create_side("collect_main_files")
        assert "DB jobs" in result
        assert "Files jobs" in result
        assert "OWID Templates/Pages" in result
        assert "bi-database-fill" in result
        assert "bi-files" in result
        assert "bi-file-earmark-richtext" in result


    def test_sidebar_contains_collect_main_files_job_link(self) -> None:
        """Test that sidebar contains Collect Templates data job link."""
        result = create_side("collect_main_files")
        assert "Collect Templates data" in result
        assert "/admin/jobs/collect_main_files" in result
        assert "bi-kanban" in result


    def test_sidebar_contains_fix_nested_main_files_job_link(self) -> None:
        """Test that sidebar contains Fix Nested Main Files job link."""
        result = create_side("fix_nested_main_files")
        assert "Fix Nested Main Files" in result
        assert "/admin/jobs/fix_nested_main_files" in result
        assert "bi-tools" in result


    def test_sidebar_marks_collect_main_files_as_active(self) -> None:
        """Test that Collect Templates data is marked as active when selected."""
        result = create_side("collect_main_files")
        # The link should have an active class
        assert "id='collect_main_files' class='active'" in result


    def test_sidebar_marks_fix_nested_main_files_as_active(self) -> None:
        """Test that Fix Nested Main Files is marked as active when selected."""
        result = create_side("fix_nested_main_files")
        # The link should have an active class
        assert "id='fix_nested_main_files' class='active'" in result
