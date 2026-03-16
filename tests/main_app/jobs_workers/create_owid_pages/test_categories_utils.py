"""
Unit tests for create_owid_pages/categoriez_extract.py module.
"""

from __future__ import annotations

from wikitextparser import WikiLink

from src.main_app.jobs_workers.create_owid_pages.categories_utils import (
    extract_categories,
    find_missing_categories,
    merge_categories,
)


def test_full_pipline() -> None:
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


class TestExtractCategories:
    def test_extract_categories(self):
        text = """
        [[Category:Category1]]
        """
        categories = extract_categories(text)
        assert categories[0].string == WikiLink('[[Category:Category1]]').string

    def test_single_category(self):
        """Should extract one category."""
        text = "[[Category:Category1]]"
        cats = extract_categories(text)

        assert len(cats) == 1
        assert cats[0].target == "Category:Category1"

    def test_multiple_categories(self):
        """Should extract multiple categories."""
        text = """
        [[Category:Cat1]]
        [[Category:Cat2]]
        [[Category:Cat3]]
        """
        cats = extract_categories(text)

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
        cats = extract_categories(text)

        assert len(cats) == 1
        assert cats[0].target == "Category:Cat1"

    def test_strip_whitespace(self):
        """Should strip whitespace around category target."""
        text = "[[Category:Cat1 ]]"
        cats = extract_categories(text)

        assert cats[0].target.strip() == "Category:Cat1"

    def test_no_categories(self):
        """Should return empty list when no categories exist."""
        text = "Normal text without categories"
        cats = extract_categories(text)

        assert cats == []


class TestFindMissingCategories:

    def test_old_category_not_in_new(self):
        """Should return category from base_categories list if it is missing in target_categories list."""
        base_categories = [WikiLink("[[Category:Cat1]]")]
        target_categories = []

        result = find_missing_categories(target_categories, base_categories)

        assert result == base_categories

    def test_category_exists_in_both(self):
        """Should not return category if it already exists in target_categories list."""
        base_categories = [WikiLink("[[Category:Cat1]]")]
        target_categories = [WikiLink("[[Category:Cat1]]")]

        result = find_missing_categories(target_categories, base_categories)

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

        result = find_missing_categories(target_categories, base_categories)

        assert len(result) == 2
        assert result[0].target == "Category:Cat1"
        assert result[1].target == "Category:Cat3"

    def test_whitespace_ignored(self):
        """Whitespace differences should be ignored."""
        base_categories = [WikiLink("[[Category:Cat1]]")]
        target_categories = [WikiLink("[[Category:Cat1 ]]")]

        result = find_missing_categories(target_categories, base_categories)

        assert result == []

    def test_empty_old(self):
        """Empty base_categories list should return empty result."""
        result = find_missing_categories([WikiLink("[[Category:Cat1]]")], [])

        assert result == []

    def test_empty_new(self):
        """Empty target_categories list should return all base_categories categories."""
        base_categories = [
            WikiLink("[[Category:Cat1]]"),
            WikiLink("[[Category:Cat2]]"),
        ]

        result = find_missing_categories([], base_categories)

        assert result == base_categories

    def test_both_empty(self):
        """Both lists empty should return empty list."""
        result = find_missing_categories([], [])

        assert result == []


class TestMergeCategories:

    def test_add_missing_category(self):
        """Should append category from old text if missing in new text."""
        new_text = "[[Category:Cat1]]"
        old_text = "Article text"

        result = merge_categories(old_text, new_text)

        assert "[[Category:Cat1]]" in result

    def test_do_not_duplicate(self):
        """Should not duplicate categories already in new text."""
        new_text = "[[Category:Cat1]]"
        old_text = """
        Article text
        [[Category:Cat1]]
        """

        result = merge_categories(old_text, new_text)

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

        result = merge_categories(old_text, new_text)

        assert "[[Category:Cat1]]" in result
        assert result.count("[[Category:Cat2]]") == 1
        assert result == new_text

    def test_no_categories_anywhere(self):
        """Should leave text unchanged when no categories exist."""
        old_text = "Old text"
        new_text = "New text"

        result = merge_categories(old_text, new_text)

        assert result == new_text
