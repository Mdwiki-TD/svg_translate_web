"""
Unit tests for src/main_app/utils/wikitext/categories_utils.py module.
"""

from __future__ import annotations

from src.main_app.utils.wikitext.categories_utils import (
    CategoryLink,
    capitalize_category,
    create_category_link_from_str,
    extract_categories,
    find_missing_categories,
    merge_categories,
    sort_categories,
)


class TestCapitalizeCategory:
    """Tests for capitalize_category."""

    def test_no_colon_returns_unchanged(self):
        """String without colon should be returned unchanged."""
        assert capitalize_category("fruit") == "fruit"

    def test_capitalizes_both_parts(self):
        """Should capitalize first letter of both namespace and name."""
        assert capitalize_category("category:apple") == "Category:Apple"

    def test_already_capitalized_stays_same(self):
        """Already capitalized input should remain unchanged."""
        assert capitalize_category("Category:Apple") == "Category:Apple"

    def test_strips_leading_trailing_whitespace(self):
        """Should strip whitespace before capitalizing."""
        assert capitalize_category("  category:apple  ") == "Category:Apple"

    def test_single_character_parts(self):
        """Single-character parts should be uppercased."""
        assert capitalize_category("c:a") == "C:A"

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert capitalize_category("") == ""

    def test_empty_parts(self):
        """Parts can be empty after split."""
        assert capitalize_category(":apple") == ":Apple"
        assert capitalize_category("fruit:") == "Fruit:"


class TestCreateCategoryLinkFromStr:
    """Tests for create_category_link_from_str."""

    def test_creates_category_link_with_correct_link_and_target(self):
        """Should create CategoryLink with expected link string and target."""
        result = create_category_link_from_str("[[Category:Foo_bar]]")
        assert isinstance(result, CategoryLink)
        assert result.link.string == "[[Category:Foo_bar]]"
        assert result.target == "Category:Foo bar"

    def test_strips_underscores_from_target(self):
        """Underscores in target should be replaced with spaces."""
        result = create_category_link_from_str("[[Category:Our_World_Data]]")
        assert result.target == "Category:Our World Data"

    def test_capitalizes_target(self):
        """Target should be capitalized."""
        result = create_category_link_from_str("[[category:apple]]")
        assert result.target == "Category:Apple"

    def test_handles_pipe_syntax(self):
        """Should handle piped category links."""
        result = create_category_link_from_str("[[Category:Foo|bar]]")
        assert result.target == "Category:Foo"


class TestExtractCategories:
    """Tests for extract_categories."""

    def test_extracts_categories_from_wikitext(self):
        """Should extract category WikiLinks from wikitext."""
        text = "[[Category:Cat1]]\n[[Category:Cat2]]"
        cats = extract_categories(text)
        assert len(cats) == 2
        assert [c.target for c in cats] == ["Category:Cat1", "Category:Cat2"]

    def test_returns_empty_list_for_non_string(self):
        """Non-string input should return empty list."""
        assert extract_categories(None) == []
        assert extract_categories(123) == []

    def test_returns_empty_for_wikitext_without_categories(self):
        """Wikitext without categories should return empty list."""
        assert extract_categories("Just some text [[Page]]") == []

    def test_handles_lowercase_category_prefix(self):
        """Lowercase [[category:...]] should be matched case-insensitively."""
        text = "[[category:foo]]"
        cats = extract_categories(text)
        assert len(cats) == 1
        assert cats[0].target == "Category:Foo"

    def test_ignores_non_category_links(self):
        """Non-category wikilinks should be ignored."""
        text = "[[Page]] [[File:img.png]] [[Category:Real]]"
        cats = extract_categories(text)
        assert len(cats) == 1
        assert cats[0].target == "Category:Real"


class TestFindMissingCategories:
    """Tests for find_missing_categories."""

    def test_empty_target_returns_all_base(self):
        """Empty target_categories should return all base_categories."""
        base = [create_category_link_from_str("[[Category:A]]"), create_category_link_from_str("[[Category:B]]")]
        result = find_missing_categories([], base)
        assert result == base

    def test_returns_only_missing_from_target(self):
        """Should return only categories in base that are not in target."""
        base = [create_category_link_from_str("[[Category:A]]"), create_category_link_from_str("[[Category:B]]")]
        target = [create_category_link_from_str("[[Category:A]]")]
        result = find_missing_categories(target, base)
        assert len(result) == 1
        assert result[0].target == "Category:B"

    def test_comparison_is_case_insensitive(self):
        """Comparison should ignore case differences."""
        base = [create_category_link_from_str("[[Category:Apple]]")]
        target = [create_category_link_from_str("[[Category:apple]]")]
        assert find_missing_categories(target, base) == []

    def test_both_empty_returns_empty(self):
        """Both empty lists should return empty list."""
        assert find_missing_categories([], []) == []

    def test_no_missing_returns_empty(self):
        """When all base categories exist in target, return empty list."""
        base = [create_category_link_from_str("[[Category:X]]")]
        target = [create_category_link_from_str("[[Category:X]]")]
        assert find_missing_categories(target, base) == []


class TestMergeCategories:
    """Tests for merge_categories."""

    def test_returns_new_text_when_old_text_empty(self):
        """Empty old_text should return new_text unchanged."""
        assert merge_categories("", "new") == "new"

    def test_returns_new_text_when_new_text_empty(self):
        """Empty new_text should return new_text (empty)."""
        assert merge_categories("old", "") == ""

    def test_returns_new_text_when_old_has_no_categories(self):
        """Old text without categories should return new_text unchanged."""
        assert merge_categories("plain text", "[[Category:A]]") == "[[Category:A]]"

    def test_appends_missing_categories_from_old_to_new(self):
        """Missing categories from old should be appended to new."""
        old = "[[Category:Old1]]"
        new = "[[Category:New1]]"
        result = merge_categories(old, new)
        assert "[[Category:New1]]" in result
        assert "[[Category:Old1]]" in result

    def test_no_missing_categories_returns_new_text_unchanged(self):
        """When old categories are already in new, return new_text as-is."""
        old = "[[Category:Shared]]"
        new = "[[Category:Shared]]"
        assert merge_categories(old, new) == new

    def test_does_not_duplicate_existing_categories(self):
        """Existing categories should not be duplicated."""
        old = "[[Category:A]] [[Category:B]]"
        new = "[[Category:A]]"
        result = merge_categories(old, new)
        assert result.count("[[Category:A]]") == 1
        assert "[[Category:B]]" in result


class TestSortCategories:
    """Tests for sort_categories."""

    def test_sorts_categories_alphabetically(self):
        """Categories should be sorted alphabetically."""
        text = "[[Category:Z]] text [[Category:A]]"
        result = sort_categories(text)
        cats = extract_categories(result)
        assert cats[0].target == "Category:A"
        assert cats[1].target == "Category:Z"

    def test_returns_original_if_no_categories(self):
        """Wikitext without categories should be returned unchanged."""
        text = "Just text"
        assert sort_categories(text) == text

    def test_removes_categories_from_original_position_and_appends_sorted(self):
        """Categories should be removed from their original positions and appended at the end sorted."""
        text = "Start [[Category:Banana]] middle [[Category:Apple]] end"
        result = sort_categories(text)
        assert "Apple" in result
        assert "Banana" in result
        assert result.index("Apple") < result.index("Banana")
        # Categories should not be in their original positions
        assert "[[Category:Banana]]" not in result.split("\n")[0]
