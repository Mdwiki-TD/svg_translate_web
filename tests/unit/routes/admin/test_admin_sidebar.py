"""Unit tests for admin_sidebar.py.

All tests that check menu content pass their own known menu through
`list_items`, so they do not depend on the real (changeable) admin menu.
"""

from __future__ import annotations

import pytest
from src.main_app.admin.admin_sidebar import create_admin_sidebar
from src.main_app.templates_markups.sidebar import SidebarGroup, SidebarItem


@pytest.fixture
def menu() -> list[SidebarGroup]:
    """A small, fixed menu used by all content tests."""
    return [
        SidebarGroup(
            id="alpha",
            title="Alpha Group",
            icon="bi-alpha",
            items=[
                SidebarItem(
                    id="item_one",
                    title="Item One",
                    icon="bi-one",
                    fallback_href="/test/one",
                    requires_admin=False,
                ),
                SidebarItem(
                    id="item_two",
                    title="Item Two",
                    icon="bi-two",
                    fallback_href="/test/two",
                    requires_admin=True,
                ),
                SidebarItem(
                    id="item_disabled",
                    title="Item Disabled",
                    fallback_href="/test/disabled",
                    disabled=True,
                ),
            ],
        ),
        SidebarGroup(
            id="beta",
            title="Beta Group",
            icon="bi-beta",
            items=[
                SidebarItem(
                    id="item_three",
                    title="Item Three",
                    icon="bi-three",
                    fallback_href="/test/three",
                    requires_admin=False,
                ),
                SidebarItem(
                    id="item_external",
                    title="Item External",
                    fallback_href="https://example.org/",
                    link_target="_blank",
                    requires_admin=False,
                ),
            ],
        ),
        SidebarGroup(
            id="admin_only",
            title="Admin Only Group",
            icon="bi-lock",
            items=[
                SidebarItem(
                    id="item_secret",
                    title="Item Secret",
                    fallback_href="/test/secret",
                    requires_admin=True,
                ),
            ],
        ),
        SidebarGroup(
            id="disabled_group",
            title="Disabled Group",
            icon="bi-x",
            disabled=True,
            items=[
                SidebarItem(
                    id="item_in_disabled",
                    title="Item In Disabled",
                    fallback_href="/test/in-disabled",
                    requires_admin=False,
                ),
            ],
        ),
    ]


class TestCreateAdminSidebarContent:
    def test_returns_html_string(self, menu) -> None:
        html = create_admin_sidebar("/test/one", is_admin=True, list_items=menu)
        assert isinstance(html, str)
        assert html.startswith("<ul")
        assert html.endswith("</ul>")

    def test_renders_group_titles_and_icons(self, menu) -> None:
        html = create_admin_sidebar("/test/one", is_admin=True, list_items=menu)
        assert "Alpha Group" in html
        assert "Beta Group" in html
        assert "bi-alpha" in html
        assert "bi-beta" in html

    def test_renders_items_titles_icons_and_hrefs(self, menu) -> None:
        html = create_admin_sidebar("/test/one", is_admin=True, list_items=menu)
        assert "Item One" in html
        assert "href='/test/one'" in html
        assert "bi-one" in html
        assert "Item Three" in html
        assert "href='/test/three'" in html

    def test_renders_desktop_and_mobile_lists(self, menu) -> None:
        html = create_admin_sidebar("/test/one", is_admin=True, list_items=menu)
        # Root <ul> + (desktop + mobile) <ul> for each of the 3 visible groups
        assert html.count("<ul") == 1 + 3 * 2

    def test_disabled_item_is_not_rendered(self, menu) -> None:
        html = create_admin_sidebar("/test/one", is_admin=True, list_items=menu)
        assert "Item Disabled" not in html
        assert "/test/disabled" not in html

    def test_disabled_group_is_not_rendered(self, menu) -> None:
        html = create_admin_sidebar("/test/one", is_admin=True, list_items=menu)
        assert "Disabled Group" not in html
        assert "Item In Disabled" not in html

    def test_external_link_has_target_and_rel(self, menu) -> None:
        html = create_admin_sidebar("/test/one", is_admin=True, list_items=menu)
        assert "target='_blank'" in html
        assert "rel='noopener noreferrer'" in html

    def test_internal_link_has_no_target(self, menu) -> None:
        only_internal = [menu[0]]
        html = create_admin_sidebar("/test/one", is_admin=True, list_items=only_internal)
        assert "target=_blank" not in html

    def test_title_is_html_escaped(self) -> None:
        group = SidebarGroup(
            id="esc",
            title="<b>Group</b>",
            icon="bi-x",
            items=[
                SidebarItem(
                    id="esc_item",
                    title="<script>alert(1)</script>",
                    fallback_href="/test/esc",
                    requires_admin=False,
                )
            ],
        )
        html = create_admin_sidebar("/test/esc", is_admin=True, list_items=[group])
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        assert "<b>Group</b>" not in html


class TestCreateAdminSidebarActive:
    def test_exact_path_marks_item_active(self, menu) -> None:
        html = create_admin_sidebar("/test/two", is_admin=True, list_items=menu)
        assert "id='item_two' class='active'" in html
        assert "id='item_one' class=''" in html
        assert "id='item_three' class=''" in html

    def test_active_item_expands_only_its_group(self, menu) -> None:
        html = create_admin_sidebar("/test/three", is_admin=True, list_items=menu)
        assert 'class="collapse show" id="beta-collapse"' in html
        assert 'class="collapse " id="alpha-collapse"' in html
        assert html.count('aria-expanded="true"') == 1

    def test_prefix_path_marks_item_active(self, menu) -> None:
        # No exact match, but the path starts with the item's href
        html = create_admin_sidebar("/test/one/details/5", is_admin=True, list_items=menu)
        assert "id='item_one' class='active'" in html
        assert 'class="collapse show" id="alpha-collapse"' in html

    def test_second_path_segment_matching_item_id_marks_it_active(self, menu) -> None:
        # path_parts[1] == "item_three" -> matched through the active_route fallback
        html = create_admin_sidebar("/admin_panel/item_three", is_admin=True, list_items=menu)
        assert "id='item_three' class='active'" in html
        assert 'class="collapse show" id="beta-collapse"' in html

    def test_exact_match_wins_over_prefix_match(self) -> None:
        group = SidebarGroup(
            id="g",
            title="G",
            icon="bi-g",
            items=[
                SidebarItem(id="short", title="Short", fallback_href="/test", requires_admin=False),
                SidebarItem(id="long", title="Long", fallback_href="/test/long", requires_admin=False),
            ],
        )
        html = create_admin_sidebar("/test/long", is_admin=True, list_items=[group])
        assert "id='long' class='active'" in html
        assert "id='short' class=''" in html

    def test_no_match_expands_first_group_without_active_item(self, menu) -> None:
        html = create_admin_sidebar("/unknown/path", is_admin=True, list_items=menu)
        assert "class='active'" not in html
        assert 'class="collapse show" id="alpha-collapse"' in html
        assert 'class="collapse " id="beta-collapse"' in html


class TestCreateAdminSidebarIsAdmin:
    def test_admin_sees_admin_only_items(self, menu) -> None:
        html = create_admin_sidebar("/test/one", is_admin=True, list_items=menu)
        assert "Item Two" in html
        assert "Item Secret" in html
        assert "Admin Only Group" in html

    def test_non_admin_does_not_see_admin_only_items(self, menu) -> None:
        html = create_admin_sidebar("/test/one", is_admin=False, list_items=menu)
        assert "Item Two" not in html
        assert "/test/two" not in html

    def test_non_admin_still_sees_public_items(self, menu) -> None:
        html = create_admin_sidebar("/test/one", is_admin=False, list_items=menu)
        assert "Item One" in html
        assert "Item Three" in html

    def test_group_with_only_admin_items_is_hidden_for_non_admin(self, menu) -> None:
        html = create_admin_sidebar("/test/one", is_admin=False, list_items=menu)
        assert "Admin Only Group" not in html
        assert "Item Secret" not in html

    def test_non_admin_with_no_visible_items_gets_empty_shell(self) -> None:
        group = SidebarGroup(
            id="locked",
            title="Locked",
            icon="bi-lock",
            items=[SidebarItem(id="secret", title="Secret", fallback_href="/s", requires_admin=True)],
        )
        html = create_admin_sidebar("/s", is_admin=False, list_items=[group])
        assert isinstance(html, str)
        assert "<ul" in html
        assert "Locked" not in html
        assert "Secret" not in html

    def test_is_admin_defaults_to_false(self, menu) -> None:
        html = create_admin_sidebar("/test/one", list_items=menu)
        assert "Item Two" not in html
        assert "Item One" in html


class TestCreateAdminSidebarUrlResolution:
    def test_uses_fallback_href_without_request_context(self, menu) -> None:
        html = create_admin_sidebar("/test/one", is_admin=True, list_items=menu)
        assert "href='/test/one'" in html

    def test_unknown_endpoint_falls_back_to_fallback_href(self, mock_app) -> None:
        group = SidebarGroup(
            id="g",
            title="G",
            icon="bi-g",
            items=[
                SidebarItem(
                    id="broken",
                    title="Broken",
                    endpoint="nonexistent.endpoint",
                    fallback_href="/fallback/broken",
                    requires_admin=False,
                )
            ],
        )
        with mock_app.test_request_context():
            html = create_admin_sidebar("/fallback/broken", is_admin=True, list_items=[group])
        assert "href='/fallback/broken'" in html
        assert "id='broken' class='active'" in html


class TestCreateAdminSidebarDefaultMenu:
    """Smoke test only: does not assert anything about the real menu content."""

    def test_default_menu_renders_valid_shell(self) -> None:
        html = create_admin_sidebar("/admin_panel/", is_admin=True)
        assert isinstance(html, str)
        assert "<ul" in html
