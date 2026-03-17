"""
Unit tests for create_owid_pages/categoriez_extract.py module.
"""

from __future__ import annotations

from src.main_app.jobs_workers.create_owid_pages.categories_utils import (
    merge_categories,
)


class TestMergeCategoriesWithSpecialChars:
    def test_add_special_category_missing(self):
        """Add a missing category with underscores to the new text."""
        new_text = "[[Category:Existing_Category]]"
        old_text = "Article [[Category:Our_World_in_Data_graphs_of_Afghanistan]]"

        result = merge_categories(old_text, new_text)

        assert "[[Category:Our_World_in_Data_graphs_of_Afghanistan]]" in result
        assert "[[Category:Existing_Category]]" in result

    def test_do_not_duplicate_special_category(self):
        """Should not duplicate a category with underscores if it already exists in new text."""
        new_text = "[[Category:Cyber_Security_Database]]"
        old_text = "Article [[Category:Cyber_Security_Database]]"

        result = merge_categories(old_text, new_text)

        # يجب أن تظهر مرة واحدة فقط (تجنب التكرار)
        count = result.count("[[Category:Cyber_Security_Database]]")
        assert count == 1

    def test_add_multiple_special_categories(self):
        """Add multiple categories with special chars that are missing."""
        new_text = "[[Category:Base_1]]"
        old_text = "Article [[Category:Base_2]] [[Category:Data_Mining_Tools]]"

        result = merge_categories(old_text, new_text)

        assert "[[Category:Base_2]]" in result
        assert "[[Category:Data_Mining_Tools]]" in result
        assert "[[Category:Base_1]]" in result

    def test_preserve_special_chars_formatting(self):
        """Ensure the added category keeps its formatting (underscores)."""
        new_text = "Text without categories"
        old_text = "Article [[Category:Complex_Category_Name_With_Multiple_Underscores]]"

        result = merge_categories(old_text, new_text)

        assert "[[Category:Complex_Category_Name_With_Multiple_Underscores]]" in result
        # التأكد من أن النص الأصلي تم إضافته كما هو دون كسر الصيغة
        assert result != new_text

    def test_long_category_name_with_underscores(self):
        """Test with a very long category name typical of OWID pages."""
        long_cat = "Category:Our_World_in_Data_graphs_of_Afghanistan_economy_overview"
        new_text = f"[{long_cat}]"  # تم كتابة الويكي لينك بشكل خاطئ في الفكرة الأصلية لتصحيحها هنا
        new_text_corrected = "[[Category:Another_Category]]"

        old_text = f"Some text [[{long_cat}]]"

        result = merge_categories(old_text, new_text_corrected)

        assert "[[Category:Another_Category]]" in result
        assert "[[Category:Our_World_in_Data_graphs_of_Afghanistan_economy_overview]]" in result

    def test_underscore_at_end_of_name(self):
        """Ensure underscores at the end of category names are handled."""
        new_text = "[[Category:Main_Page]]"
        old_text = "Article [[Category:Main_Page_extra]]"

        result = merge_categories(old_text, new_text)

        assert "[[Category:Main_Page_extra]]" in result


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
