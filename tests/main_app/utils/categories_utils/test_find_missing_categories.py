"""
Unit tests for create_owid_pages/categoriez_extract.py module.
"""

from __future__ import annotations

from src.main_app.utils.wikitext.categories_utils import (
    create_category_link_from_str,
    find_missing_categories,
)


class TestFindMissingCategories:

    def test_old_category_not_in_new(self):
        """Should return category from base_categories list if it is missing in target_categories list."""
        base_categories = [create_category_link_from_str("[[Category:Cat1]]")]
        target_categories = []

        result = find_missing_categories(target_categories, base_categories)

        assert result == base_categories

    def test_category_exists_in_both(self):
        """Should not return category if it already exists in target_categories list."""
        base_categories = [create_category_link_from_str("[[Category:cat1]]")]
        target_categories = [create_category_link_from_str("[[Category:Cat1]]")]

        result = find_missing_categories(target_categories, base_categories)

        assert result == []

    def test_multiple_categories(self):
        """Should return only base_categories categories that are not present in target_categories."""
        base_categories = [
            create_category_link_from_str("[[Category:Cat1]]"),
            create_category_link_from_str("[[ category:cat2 ]]"),
            create_category_link_from_str("[[Category:Cat3]]"),
        ]

        target_categories = [
            create_category_link_from_str("[[Category:Cat2]]"),
        ]

        result = find_missing_categories(target_categories, base_categories)

        assert len(result) == 2
        assert result[0].target == "Category:Cat1"
        assert result[1].target == "Category:Cat3"

    def test_whitespace_ignored(self):
        """Whitespace differences should be ignored."""
        base_categories = [create_category_link_from_str("[[Category:Cat1 new 2020{{!}}]]")]
        target_categories = [create_category_link_from_str("[[ Category:Cat1 new 2020{{!}}]]")]

        result = find_missing_categories(target_categories, base_categories)

        assert result == []

    def test_empty_old(self):
        """Empty base_categories list should return empty result."""
        result = find_missing_categories([create_category_link_from_str("[[Category:cat1]]")], [])

        assert result == []

    def test_empty_new(self):
        """Empty target_categories list should return all base_categories categories."""
        base_categories = [
            create_category_link_from_str("[[Category:Cat1 new]]"),
            create_category_link_from_str("[[Category:Cat2]]"),
        ]

        result = find_missing_categories([], base_categories)

        assert result == base_categories

    def test_both_empty(self):
        """Both lists empty should return empty list."""
        result = find_missing_categories([], [])

        assert result == []


class TestFindMissingCategoriesWithSpecialChars:
    def test_old_has_special_new_missing(self):
        """Old text has a category with underscore, new text is missing it."""
        # use create_category_link_from_str directly to ensure control over the data
        base_categories = [create_category_link_from_str("[[Category:Our_World_in_Data_graphs_of_Afghanistan]]")]
        target_categories = []

        result = find_missing_categories(target_categories, base_categories)

        assert len(result) == 1
        assert result[0].target == "Category:Our World in Data graphs of Afghanistan"

    def test_old_has_special_new_present(self):
        """If both have the same category with underscore, it should not be missing."""
        base_categories = [create_category_link_from_str("[[Category:Cyber Security]]")]
        target_categories = [create_category_link_from_str("[[Category:Cyber_Security]]")]

        result = find_missing_categories(target_categories, base_categories)
        assert len(result) == 0

    def test_special_chars_case_insensitive_matching(self):
        """Ensure matching works correctly even if case varies (standard wiki behavior)."""
        # In Wiki, lists are usually case-insensitive but encoding is important.
        # Here we verify that underscores don't break comparison if names match.
        base_categories = [create_category_link_from_str("[[Category:test_Data]]")]
        target_categories = [create_category_link_from_str("[[Category:Test_Data]]")]

        # Note: wtp behavior depends on settings, but the logic here is to ensure no duplicate addition
        result = find_missing_categories(target_categories, base_categories)
        # Usually it should not be considered missing if semantically identical, but per current code logic:
        # Should return zero (0) as the text was encoded or compared as strings.
        assert len(result) == 0

    def test_multiple_missing_with_underscores(self):
        """Missing multiple categories with underscores."""
        base_categories = [
            create_category_link_from_str("[[Category:afghanistan|2020]]"),
            create_category_link_from_str("[[Category:Economy_Data]]")
        ]
        target_categories = [
            create_category_link_from_str("[[Category:Afghanistan]]")
            # Economy_Data missing
        ]

        result = find_missing_categories(target_categories, base_categories)
        assert len(result) == 1
        assert result[0].target == "Category:Economy Data"
