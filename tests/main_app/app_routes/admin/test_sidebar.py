"""Tests for sidebar helpers."""

import pytest

from src.main_app.app_routes.admin import sidebar


def test_generate_list_item() -> None:
    html = sidebar.generate_list_item("/home", "Home", icon="bi-house", target=True)

    assert "href='/home'" in html
    assert "bi-house" in html
    assert "target='_blank'" in html
    assert "Home" in html


def test_create_side_marks_active_item() -> None:
    html = sidebar.create_side("coordinators")

    assert "Tasks" in html
    assert "coordinators" in html
    assert "active" in html
    assert html.count("<ul") >= 2


def test_generate_list_item_basic():
    """
    Tests basic list item generation.
    """
    result = sidebar.generate_list_item("/home", "Home")
    assert "href='/home'" in result
    assert "title='Home'" in result
    assert "<i class" not in result
    assert "target=" not in result
    assert "<span class='hide-on-collapse-inline'>Home</span>" in result


def test_generate_list_item_with_icon():
    """
    Tests list item generation with an icon.
    """
    result = sidebar.generate_list_item("/home", "Home", icon="bi-house")
    assert "href='/home'" in result
    assert "title='Home'" in result
    assert "<i class='bi bi-house me-1'></i>" in result
    assert "target=" not in result
    assert "<span class='hide-on-collapse-inline'>Home</span>" in result


def test_generate_list_item_with_target():
    """
    Tests list item generation with a target attribute.
    """
    result = sidebar.generate_list_item("/home", "Home", target="_blank")
    assert "href='/home'" in result
    assert "title='Home'" in result
    assert "<i class" not in result
    assert "target='_blank'" in result
    assert "<span class='hide-on-collapse-inline'>Home</span>" in result


def test_generate_list_item_with_icon_and_target():
    """
    Tests list item generation with both an icon and a target attribute.
    """
    result = sidebar.generate_list_item("/home", "Home", icon="bi-house", target="_blank")
    assert "href='/home'" in result
    assert "title='Home'" in result
    assert "<i class='bi bi-house me-1'></i>" in result
    assert "target='_blank'" in result
    assert "<span class='hide-on-collapse-inline'>Home</span>" in result


@pytest.mark.skip(reason="Sidebar are currently expanded.")
def test_create_side_no_active_item():
    """
    Tests sidebar creation with no active item.
    """
    result = sidebar.create_side("non-existent")
    assert "class='active'" not in result
    assert 'aria-expanded="false"' in result
    assert 'class="collapse "' in result


def test_create_side_with_active_item():
    """
    Tests sidebar creation with an active item.
    """
    result = sidebar.create_side("recent")
    assert "id='last' class='active'" in result
    assert 'aria-expanded="true"' in result
    assert 'class="collapse show"' in result


def test_sidebar_contains_jobs_section():
    """Test that sidebar contains the Jobs section."""
    result = sidebar.create_side("collect_main_files/list")
    assert "Jobs" in result
    assert "bi-gear-fill" in result


def test_sidebar_contains_collect_main_files_job_link():
    """Test that sidebar contains Collect Main Files job link."""
    result = sidebar.create_side("collect_main_files/list")
    assert "Collect Main Files" in result
    assert "collect_main_files/list" in result
    assert "bi-kanban" in result


def test_sidebar_contains_fix_nested_main_files_job_link():
    """Test that sidebar contains Fix Nested Main Files job link."""
    result = sidebar.create_side("fix_nested_main_files/list")
    assert "Fix Nested Main Files" in result
    assert "fix_nested_main_files/list" in result
    assert "bi-tools" in result


def test_sidebar_contains_download_main_files_job_link():
    """Test that sidebar contains Download Main Files job link."""
    result = sidebar.create_side("download_main_files/list")
    assert "Download Main Files" in result
    assert "download_main_files/list" in result
    assert "bi-download" in result


def test_sidebar_marks_collect_main_files_as_active():
    """Test that Collect Main Files is marked as active when selected."""
    result = sidebar.create_side("collect_main_files/list")
    # The link should have an active class
    assert "id='collect_main_files' class='active'" in result


def test_sidebar_marks_fix_nested_main_files_as_active():
    """Test that Fix Nested Main Files is marked as active when selected."""
    result = sidebar.create_side("fix_nested_main_files/list")
    # The link should have an active class
    assert "id='fix_nested_main_files' class='active'" in result


def test_sidebar_marks_download_main_files_as_active():
    """Test that Download Main Files is marked as active when selected."""
    result = sidebar.create_side("download_main_files/list")
    # The link should have an active class
    assert "id='download_main_files' class='active'" in result


def test_sidebar_has_all_three_job_types():
    """Test that sidebar has all three job types."""
    result = sidebar.create_side("templates")
    assert "Collect Main Files" in result
    assert "Fix Nested Main Files" in result
    assert "Download Main Files" in result
    assert result.count("/list") >= 3  # At least 3 job list links
