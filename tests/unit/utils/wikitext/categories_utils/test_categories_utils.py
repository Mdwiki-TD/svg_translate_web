"""
Unit tests for create_owid_pages/categoriez_extract.py module.
"""

from __future__ import annotations

from src.main_app.utils.wikitext.categories_utils import (
    create_category_link_from_str,
    extract_categories,
    find_missing_categories,
    merge_categories,
    merge_categories_into_text,
)


def test_full_pipeline() -> None:
    """Should append multiple missing categories."""
    new_text = """
    [[Category:Cat1]]
    [[Category:Cat2]]
    """

    old_text = """
    Article text
    [[Category:Cat2]]
    """

    new_cats = extract_categories(new_text)
    old_cats = extract_categories(old_text)

    assert len(new_cats) == 2
    assert len(old_cats) == 1

    missing_categories = find_missing_categories(
        base_categories=old_cats,
        target_categories=new_cats,
    )

    assert missing_categories == []

    result = merge_categories(old_text, new_text)

    assert "[[Category:Cat1]]" in result
    assert result.count("[[Category:Cat2]]") == 1
    assert result == new_text


def test_full_pipeline_2() -> None:
    """Should append multiple missing categories."""
    new_text = """[[Category:Cat1]][[Category:Cat2]]"""

    old_text = """
    Article text
    [[Category:Cat2]]
    [[Category:Cat3 | test ]]
    """

    new_cats = extract_categories(new_text)
    old_cats = extract_categories(old_text)

    assert len(new_cats) == 2
    assert len(old_cats) == 2

    missing_categories = find_missing_categories(
        base_categories=old_cats,
        target_categories=new_cats,
    )

    assert missing_categories[0].target == create_category_link_from_str("[[Category:Cat3 | test ]]").target

    result = merge_categories(old_text, new_text)

    assert "[[Category:Cat1]]" in result
    assert result.count("[[Category:Cat2]]") == 1

    expected_text = """[[Category:Cat1]][[Category:Cat2]]\n[[Category:Cat3 | test ]]"""

    assert result.strip() == expected_text.strip()

class TestMergeCategoriesIntoText:
    """Tests for merge_categories_into_text function."""

    def test_returns_empty_string_when_text_is_empty(self):
        """Empty text should be returned as-is."""
        assert merge_categories_into_text(["Category:Cat1"], "") == ""

    def test_returns_none_when_text_is_none(self):
        """None text should be returned as-is (falsy guard)."""
        assert merge_categories_into_text(["Category:Cat1"], None) is None  # type: ignore[arg-type]

    def test_returns_text_unchanged_when_text_has_no_categories(self):
        """When text has no existing categories, the function returns it unchanged (known TODO)."""
        text = "Some article content without categories."
        result = merge_categories_into_text(["Category:Cat1"], text)
        assert result == text

    def test_appends_missing_category(self):
        """A category not already in the text should be appended."""
        text = "Content\n[[Category:Cat1]]"
        result = merge_categories_into_text(["Category:Cat2"], text)
        assert "[[Category:Cat1]]" in result
        assert "Category:Cat2" in result

    def test_does_not_duplicate_existing_category(self):
        """A category already present should not be appended again."""
        text = "Content\n[[Category:Cat1]]"
        result = merge_categories_into_text(["Category:Cat1"], text)
        assert result == text

    def test_appends_only_missing_when_mixed(self):
        """When some categories exist and some don't, only the missing ones are appended."""
        text = "Content\n[[Category:Cat1]]\n[[Category:Cat2]]"
        result = merge_categories_into_text(
            ["Category:Cat1", "Category:Cat3", "Category:Cat4"], text
        )
        # Cat1 already present — should not appear a second time
        assert result.count("Category:Cat1") == 1
        # Cat3 and Cat4 should be appended
        assert "Category:Cat3" in result
        assert "Category:Cat4" in result

    def test_returns_text_unchanged_when_all_categories_exist(self):
        """If every category in cats_list is already in text, text is returned unchanged."""
        text = "Content\n[[Category:Cat1]]\n[[Category:Cat2]]"
        result = merge_categories_into_text(["Category:Cat1", "Category:Cat2"], text)
        assert result == text

    def test_empty_cats_list_does_not_modify_text(self):
        """An empty cats_list should leave the text untouched."""
        text = "Content\n[[Category:Cat1]]"
        result = merge_categories_into_text([], text)
        assert result == text

    def test_appended_categories_are_newline_separated(self):
        """Multiple appended categories should each appear on their own line."""
        text = "Content\n[[Category:Cat1]]"
        result = merge_categories_into_text(["Category:Cat2", "Category:Cat3"], text)
        lines = result.strip().split("\n")
        # Last two lines should be the new categories
        assert "Cat2" in lines[-2] or "Cat2" in lines[-1]
        assert "Cat3" in lines[-1] or "Cat3" in lines[-2]

    def test_category_comparison_is_case_insensitive(self):
        """'Category:cat1' in text should match 'Category:Cat1' in cats_list."""
        text = "Content\n[[Category:cat1]]"
        result = merge_categories_into_text(["Category:Cat1"], text)
        # Should be treated as already present
        assert result == text

    def test_preserves_original_text_content(self):
        """Non-category content in the text must not be altered."""
        text = "Some important paragraph.\n\n== Section ==\nMore text.\n[[Category:Existing]]"
        result = merge_categories_into_text(["Category:New"], text)
        assert "Some important paragraph." in result
        assert "== Section ==" in result
        assert "More text." in result
