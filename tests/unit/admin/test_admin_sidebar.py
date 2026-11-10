"""Unit tests for admin_sidebar.py."""

from __future__ import annotations

from src.main_app.admin.admin_sidebar import (
    create_admin_sidebar,
)


class TestCreateSide:
    def test_returns_html_string(self, mock_app):
        with mock_app.test_request_context():
            html = create_admin_sidebar("admins", is_admin=True)
            assert isinstance(html, str)
            assert "<ul" in html

    def test_contains_admins_link(self, mock_app):
        with mock_app.test_request_context():
            html = create_admin_sidebar("admins", is_admin=True)
            assert "Admins" in html

    def test_contains_users_link(self, mock_app):
        with mock_app.test_request_context():
            html = create_admin_sidebar("admins", is_admin=True)
            assert "Users" in html

    def test_create_side_marks_active_item(self) -> None:
        html = create_admin_sidebar("/adminpanel/templates/", is_admin=True)

        assert "Admins" in html
        assert "active" in html
        assert html.count("<ul") >= 2

    def test_create_side_with_active_item(self) -> None:
        """
        Tests sidebar creation with an active item.
        """
        result = create_admin_sidebar("admins", is_admin=True)
        assert 'aria-expanded="true"' in result
        assert 'class="collapse show"' in result

    def test_sidebar_contains_jobs_section(self) -> None:
        """Test that sidebar contains the Jobs section."""
        result = create_admin_sidebar("collect_templates_data", is_admin=True)
        assert "DB Jobs" in result
        assert "Files Jobs" in result
        assert "OWID Templates/Pages" in result
        assert "bi-database-fill" in result
        assert "bi-files" in result
        assert "bi-file-earmark-richtext" in result

    def test_sidebar_contains_collect_templates_data_job_link(self) -> None:
        """Test that sidebar contains Collect Templates data job link."""
        result = create_admin_sidebar("collect_templates_data", is_admin=True)
        assert "Collect Templates data" in result
        assert "/adminpanel/jobs/collect_templates_data" in result
        assert "bi-kanban" in result

    def test_sidebar_contains_fix_nested_main_files_job_link(self) -> None:
        """Test that sidebar contains Fix Nested Main Files job link."""
        result = create_admin_sidebar("fix_nested_main_files", is_admin=True)
        assert "Fix Nested Main Files" in result
        assert "/adminpanel/jobs/fix_nested_main_files" in result
        assert "bi-tools" in result

    def test_sidebar_marks_collect_templates_data_as_active(self) -> None:
        """Test that Collect Templates data is marked as active when selected."""
        result = create_admin_sidebar("/adminpanel/jobs/collect_templates_data", is_admin=True)
        # The link should have an active class
        assert "id='collect_templates_data' class='active'" in result

    def test_sidebar_marks_fix_nested_main_files_as_active(self) -> None:
        """Test that Fix Nested Main Files is marked as active when selected."""
        result = create_admin_sidebar("/adminpanel/jobs/fix_nested_main_files", is_admin=True)
        # The link should have an active class
        assert "id='fix_nested_main_files' class='active'" in result


class TestCreateSideIsAdmin:
    """Tests for the new `is_admin` filtering behavior."""

    def test_admin_items_visible_by_default(self) -> None:
        result = create_admin_sidebar("/adminpanel/templates/", is_admin=True)
        assert "Templates" in result

    def test_admin_items_hidden_for_non_admin(self) -> None:
        result = create_admin_sidebar("/adminpanel/templates/", is_admin=False)
        assert "Templates" not in result

    def test_non_admin_still_returns_valid_shell(self) -> None:
        result = create_admin_sidebar("/adminpanel/templates/", is_admin=False)
        assert isinstance(result, str)
        assert "<ul" in result
