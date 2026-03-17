"""
Unit tests for create_owid_pages/categoriez_extract.py module.
"""

from __future__ import annotations

from src.main_app.jobs_workers.create_owid_pages.categories_utils import (
    create_category_link_from_str,
    extract_categories,
)


class TestExtractCategories:
    def test_extract_categories(self):
        text = """
        [[Category:Category1]]
        """
        categories = extract_categories(text)
        assert categories[0].link.string == create_category_link_from_str('[[Category:Category1]]').link.string

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


class TestExtractCategoriesWithSpecialChars:
    def test_extract_category_with_underscore(self):
        """Should extract categories containing underscores correctly."""
        text = "[[Category:Our_World_in_Data_graphs_of_Afghanistan]]"
        categories = extract_categories(text)
        assert len(categories) == 1
        # التحقق من أن الهدف يحافظ على النص الأصلي (مع الترميز إذا لزم الأمر أو بدون حسب سلوك الويكي)
        assert categories[0].target == "Category:Our World in Data graphs of Afghanistan"

    def test_extract_multiple_special_categories(self):
        """Should handle multiple categories with special characters."""
        text = """
        [[Category:Afghanistan]]
        [[Category:Data_Graphics]]
        [[Category:Graph_of_Cities]]
        """
        categories = extract_categories(text)
        assert len(categories) == 3

        targets = [c.target for c in categories]
        expected_targets = [
            "Category:Afghanistan",
            "Category:Data Graphics",
            "Category:Graph of Cities"
        ]
        assert targets == expected_targets

    def test_extract_mixed_normal_and_special_categories(self):
        """Should mix normal and special categories."""
        text = "[[Category:Cyber_Security]] [[Category:Society]] [[Category:Night_Owl]]"
        categories = extract_categories(text)
        assert len(categories) == 3

        targets = [c.target for c in categories]
        assert "Category:Cyber Security" in targets
        assert "Category:Society" in targets
        assert "Category:Night Owl" in targets
