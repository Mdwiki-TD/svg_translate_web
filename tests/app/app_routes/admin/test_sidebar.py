"""Tests for sidebar helpers."""

from src.app.app_routes.admin import sidebar


def test_generate_list_item() -> None:
    html = sidebar.generate_list_item("/home", "Home", icon="bi-house", target=True)

    assert "href='/home'" in html
    assert "bi-house" in html
    assert "target='_blank'" in html
    assert "Home" in html


def test_create_side_marks_active_item() -> None:
    html = sidebar.create_side("coordinators")

    assert "Users" in html
    assert "coordinators" in html
    assert "active" in html
    assert html.count("<ul") >= 2
