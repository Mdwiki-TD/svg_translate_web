"""Unit tests for rename_owid_pages/objects module."""

from __future__ import annotations

from src.main_app.jobs_workers.admin_jobs_workers.rename_owid_pages.objects import RenameInfo

# ── tests: RenameInfo.needs_rename ───────────────────────────────────────────────────────────


class TestNeedsRename:
    def test_lowercase_first_char_returns_true(self):
        info = RenameInfo(namespace=0, old_title="Template:OWID/daily_meat_consumption", full_prefix="Template:OWID/")

        assert info.needs_rename() is True
        assert info.new_title == "Template:OWID/Daily_meat_consumption"

    def test_uppercase_first_char_returns_false(self):
        info = RenameInfo(namespace=0, old_title="Template:OWID/Daily_meat_consumption", full_prefix="Template:OWID/")
        assert info.needs_rename() is False
        assert info.new_title == ""

    def test_non_alpha_first_char_returns_false(self):
        info = RenameInfo(namespace=0, old_title="Template:OWID/123_data", full_prefix="Template:OWID/")
        assert info.needs_rename() is False
        assert info.new_title == ""

    def test_title_not_starting_with_prefix_returns_false(self):
        info = RenameInfo(namespace=0, old_title="Template:Other/something", full_prefix="Template:OWID/")
        assert info.needs_rename() is False
        assert info.new_title == ""

    def test_empty_after_prefix_returns_false(self):
        info = RenameInfo(namespace=0, old_title="Template:OWID/", full_prefix="Template:OWID/")
        assert info.needs_rename() is False
        assert info.new_title == ""

    def test_main_namespace_prefix(self):
        info = RenameInfo(namespace=0, old_title="OWID/some_page", full_prefix="OWID/")
        assert info.needs_rename() is True
        assert info.new_title == "OWID/Some_page"

    def test_preserves_underscores_and_spaces(self):
        info = RenameInfo(namespace=0, old_title="Template:OWID/snake_case_name", full_prefix="Template:OWID/")
        assert info.needs_rename() is True
        assert info.new_title == "Template:OWID/Snake_case_name"


# ── tests: RenameInfo ─────────────────────────────────────────────────────────


class TestRenameInfo:
    def test_default_values(self):
        info = RenameInfo(namespace=0, old_title="Old")
        assert info.namespace == 0
        assert info.old_title == "Old"
        assert info.new_title == ""
        assert info.status == "pending"
        assert info.msg == ""
        assert info.newrevid is None
        assert info.timestamp

    def test_to_json(self):
        info = RenameInfo(namespace=10, old_title="Old", new_title="New", status="renamed", msg="ok")
        d = info.to_json()
        assert d["namespace"] == 10
        assert d["old_title"] == "Old"
        assert d["new_title"] == "New"
        assert d["status"] == "renamed"
        assert d["msg"] == "ok"
        assert "timestamp" in d
