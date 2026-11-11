"""Unit tests for src/main_app/templates_markups/sidebar/sidebar.py."""

from __future__ import annotations

from src.main_app.templates_markups.sidebar.sidebar import (
    SidebarItem,
    generate_list_item,
)


class TestSidebarItem:
    def test_create(self):
        item = SidebarItem(
            id="test",
            title="Test",
            fallback_href="/test",
            requires_admin=False,
        )
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
        # mock_app.add_url_rule("/admin_panel/settings/", endpoint="admin_panel.settings.dashboard")
        item = SidebarItem(
            id="settings",
            title="Settings",
            endpoint="admin_panel.settings.dashboard",
            fallback_href="/admin_panel/settings/",
        )
        with mock_app.test_request_context():
            assert item.resolve_href() == "/admin_panel/settings/"

    def test_resolve_href_falls_back_on_missing_endpoint(self, mock_app):
        item = SidebarItem(
            id="missing",
            title="Missing",
            endpoint="does.not.exist",
            fallback_href="/admin_panel/missing",
        )
        with mock_app.test_request_context():
            assert item.resolve_href() == "/admin_panel/missing"

    def test_resolve_href_uses_fallback_outside_request_context(self):
        item = SidebarItem(
            id="settings",
            title="Settings",
            endpoint="admin_panel.settings.dashboard",
            fallback_href="/admin_panel/settings/",
        )
        assert item.resolve_href() == "/admin_panel/settings/"


class TestGenerateListItem:
    def test_basic_link(self):
        item = SidebarItem(
            id="test",
            fallback_href="/test",
            title="Test Page",
            icon=None,
            link_target=None,
            disabled=False,
        )
        html = generate_list_item(item)
        assert "/test" in html
        assert "Test Page" in html
        assert "<a" in html

    def test_with_icon(self):
        item = SidebarItem(
            id="test",
            fallback_href="/test",
            title="Test",
            icon="bi-gear",
            link_target=None,
            disabled=False,
        )
        html = generate_list_item(item)
        assert "bi-gear" in html

    def test_with_target_blank(self):
        item = SidebarItem(
            id="test",
            fallback_href="/test",
            title="Test",
            icon="bi-gear",
            link_target="_blank",
            disabled=False,
        )
        html = generate_list_item(item)
        assert "target='_blank'" in html

    def test_with_target_blank_has_noopener_rel(self):
        item = SidebarItem(
            id="test",
            fallback_href="/test",
            title="Test",
            icon="bi-gear",
            link_target="_blank",
            disabled=False,
        )
        html = generate_list_item(item)
        assert "rel='noopener noreferrer'" in html

    def test_no_target_by_default(self):
        item = SidebarItem(
            id="test",
            fallback_href="/test",
            title="Test",
            icon=None,
            link_target=None,
            disabled=False,
        )
        html = generate_list_item(item)
        assert "target=" not in html

    def test_generate_list_item(self) -> None:
        item = SidebarItem(
            id="home",
            fallback_href="/home",
            title="Home",
            icon="bi-house",
            link_target="_blank",
            disabled=False,
        )
        html = generate_list_item(item)
        assert "/home" in html
        assert "bi-house" in html
        assert "target='_blank'" in html
        assert "Home" in html

    def test_generate_list_item_basic(self) -> None:
        item = SidebarItem(
            id="home",
            fallback_href="/admin_panel/home",
            title="Home",
            icon=None,
            link_target=None,
            disabled=False,
        )
        result = generate_list_item(item)
        assert "/admin_panel/home" in result
        assert "title='Home'" in result
        assert "<i class" not in result
        assert "target=" not in result
        assert "<span class='hide-on-collapse-inline'>Home</span>" in result

    def test_generate_list_item_with_icon(self) -> None:
        item = SidebarItem(
            id="home",
            fallback_href="/admin_panel/home",
            title="Home",
            icon="bi-house",
            link_target=None,
            disabled=False,
        )
        result = generate_list_item(item)
        assert "/admin_panel/home" in result
        assert "title='Home'" in result
        assert "<i class='bi bi-house me-1'></i>" in result
        assert "target=" not in result
        assert "<span class='hide-on-collapse-inline'>Home</span>" in result

    def test_generate_list_item_with_target(self) -> None:
        item = SidebarItem(
            id="home",
            fallback_href="/home",
            title="Home",
            icon=None,
            link_target="_blank",
            disabled=False,
        )
        result = generate_list_item(item)
        assert "/home" in result
        assert "title='Home'" in result
        assert "<i class" not in result
        assert "target='_blank'" in result
        assert "<span class='hide-on-collapse-inline'>Home</span>" in result

    def test_generate_list_item_with_icon_and_target(self) -> None:
        item = SidebarItem(
            id="home",
            fallback_href="/home",
            title="Home",
            icon="bi-house",
            link_target="_blank",
            disabled=False,
        )
        result = generate_list_item(item)
        assert "/home" in result
        assert "title='Home'" in result
        assert "<i class='bi bi-house me-1'></i>" in result
        assert "target='_blank'" in result
        assert "<span class='hide-on-collapse-inline'>Home</span>" in result
