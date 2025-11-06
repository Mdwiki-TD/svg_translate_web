"""
Tests for sidebar generation functions.
"""

from src.app.app_routes.admin.sidebar import generate_list_item, create_side


def test_generate_list_item_basic():
    """
    Tests basic list item generation.
    """
    result = generate_list_item("/home", "Home")
    assert "href='/home'" in result
    assert "title='Home'" in result
    assert "<i class" not in result
    assert "target=" not in result
    assert "<span class='hide-on-collapse-inline'>Home</span>" in result


def test_generate_list_item_with_icon():
    """
    Tests list item generation with an icon.
    """
    result = generate_list_item("/home", "Home", icon="bi-house")
    assert "href='/home'" in result
    assert "title='Home'" in result
    assert "<i class='bi bi-house me-1'></i>" in result
    assert "target=" not in result
    assert "<span class='hide-on-collapse-inline'>Home</span>" in result


def test_generate_list_item_with_target():
    """
    Tests list item generation with a target attribute.
    """
    result = generate_list_item("/home", "Home", target="_blank")
    assert "href='/home'" in result
    assert "title='Home'" in result
    assert "<i class" not in result
    assert "target='_blank'" in result
    assert "<span class='hide-on-collapse-inline'>Home</span>" in result


def test_generate_list_item_with_icon_and_target():
    """
    Tests list item generation with both an icon and a target attribute.
    """
    result = generate_list_item("/home", "Home", icon="bi-house", target="_blank")
    assert "href='/home'" in result
    assert "title='Home'" in result
    assert "<i class='bi bi-house me-1'></i>" in result
    assert "target='_blank'" in result
    assert "<span class='hide-on-collapse-inline'>Home</span>" in result


def test_create_side_no_active_item():
    """
    Tests sidebar creation with no active item.
    """
    result = create_side("non-existent")
    assert "class='active'" not in result
    assert 'aria-expanded="false"' in result
    assert 'class="collapse "' in result


def test_create_side_with_active_item():
    """
    Tests sidebar creation with an active item.
    """
    result = create_side("recent")
    assert "id='last' class='active'" in result
    assert 'aria-expanded="true"' in result
    assert 'class="collapse show"' in result
