"""
Unit tests for create_owid_pages/categoriez_extract.py module.
"""

from __future__ import annotations

import pytest
from wikitextparser import WikiLink

from src.main_app.jobs_workers.create_owid_pages.categories_utils import (
    _extract_categories,
    extract_categories_list,
    extend_categories,
)


class TestExtractCategories:
    def test_extract_categories(self):
        text = """
        [[Category:Category1]]
        """
        categories = _extract_categories(text)
        assert categories[0].string == WikiLink('[[Category:Category1]]').string

    def test_single_category(self):
        """Should extract one category."""
        text = "[[Category:Category1]]"
        cats = _extract_categories(text)

        assert len(cats) == 1
        assert cats[0].target == "Category:Category1"

    def test_multiple_categories(self):
        """Should extract multiple categories."""
        text = """
        [[Category:Cat1]]
        [[Category:Cat2]]
        [[Category:Cat3]]
        """
        cats = _extract_categories(text)

        assert len(cats) == 3
        assert [c.target for c in cats] == [
            "Category:Cat1",
            "Category:Cat2",
            "Category:Cat3",
        ]

    def test_ignore_non_category_links(self):
        """Should ignore normal wikilinks."""
        text = """
        [[Page1]]
        [[Category:Cat1]]
        [[File:Example.png]]
        """
        cats = _extract_categories(text)

        assert len(cats) == 1
        assert cats[0].target == "Category:Cat1"

    def test_strip_whitespace(self):
        """Should strip whitespace around category target."""
        text = "[[Category:Cat1 ]]"
        cats = _extract_categories(text)

        assert cats[0].target.strip() == "Category:Cat1"

    def test_no_categories(self):
        """Should return empty list when no categories exist."""
        text = "Normal text without categories"
        cats = _extract_categories(text)

        assert cats == []


class TestExtractCategoriesList:

    def test_old_category_not_in_new(self):
        """Should return category from base_categories list if it is missing in target_categories list."""
        base_categories = [WikiLink("[[Category:Cat1]]")]
        target_categories = []

        result = extract_categories_list(target_categories, base_categories)

        assert result == base_categories

    def test_category_exists_in_both(self):
        """Should not return category if it already exists in target_categories list."""
        base_categories = [WikiLink("[[Category:Cat1]]")]
        target_categories = [WikiLink("[[Category:Cat1]]")]

        result = extract_categories_list(target_categories, base_categories)

        assert result == []

    def test_multiple_categories(self):
        """Should return only base_categories categories that are not present in target_categories."""
        base_categories = [
            WikiLink("[[Category:Cat1]]"),
            WikiLink("[[Category:Cat2]]"),
            WikiLink("[[Category:Cat3]]"),
        ]

        target_categories = [
            WikiLink("[[Category:Cat2]]"),
        ]

        result = extract_categories_list(target_categories, base_categories)

        assert len(result) == 2
        assert result[0].target == "Category:Cat1"
        assert result[1].target == "Category:Cat3"

    def test_whitespace_ignored(self):
        """Whitespace differences should be ignored."""
        base_categories = [WikiLink("[[Category:Cat1]]")]
        target_categories = [WikiLink("[[Category:Cat1 ]]")]

        result = extract_categories_list(target_categories, base_categories)

        assert result == []

    def test_empty_old(self):
        """Empty base_categories list should return empty result."""
        result = extract_categories_list([WikiLink("[[Category:Cat1]]")], [])

        assert result == []

    def test_empty_new(self):
        """Empty target_categories list should return all base_categories categories."""
        base_categories = [
            WikiLink("[[Category:Cat1]]"),
            WikiLink("[[Category:Cat2]]"),
        ]

        result = extract_categories_list([], base_categories)

        assert result == base_categories

    def test_both_empty(self):
        """Both lists empty should return empty list."""
        result = extract_categories_list([], [])

        assert result == []


class TestExtendCategories:

    def test_add_missing_category(self):
        """Should append category from old text if missing in new text."""
        new_text = "[[Category:Cat1]]"
        old_text = "Article text"

        result = extend_categories(old_text, new_text)

        assert "[[Category:Cat1]]" in result

    def test_do_not_duplicate(self):
        """Should not duplicate categories already in new text."""
        new_text = "[[Category:Cat1]]"
        old_text = """
        Article text
        [[Category:Cat1]]
        """

        result = extend_categories(old_text, new_text)

        assert result.count("[[Category:Cat1]]") == 1

    def test_multiple_categories(self):
        """Should append multiple missing categories."""
        new_text = """
        [[Category:Cat1]]
        [[Category:Cat2]]
        """

        old_text = """
        Article text
        [[Category:Cat2]]
        """

        result = extend_categories(old_text, new_text)

        assert "[[Category:Cat1]]" in result
        assert result.count("[[Category:Cat2]]") == 1

    def test_no_categories_anywhere(self):
        """Should leave text unchanged when no categories exist."""
        old_text = "Old text"
        new_text = "New text"

        result = extend_categories(old_text, new_text)

        assert result == "New text\n"
