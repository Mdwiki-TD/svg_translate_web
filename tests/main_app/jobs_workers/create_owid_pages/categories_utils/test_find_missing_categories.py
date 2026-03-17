"""
Unit tests for create_owid_pages/categoriez_extract.py module.
"""

from __future__ import annotations

from src.main_app.jobs_workers.create_owid_pages.categories_utils import (
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
        base_categories = [create_category_link_from_str("[[Category:Cat1]]")]
        target_categories = [create_category_link_from_str("[[Category:Cat1]]")]

        result = find_missing_categories(target_categories, base_categories)

        assert result == []

    def test_multiple_categories(self):
        """Should return only base_categories categories that are not present in target_categories."""
        base_categories = [
            create_category_link_from_str("[[Category:Cat1]]"),
            create_category_link_from_str("[[Category:Cat2]]"),
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
        base_categories = [create_category_link_from_str("[[Category:Cat1]]")]
        target_categories = [create_category_link_from_str("[[Category:Cat1 ]]")]

        result = find_missing_categories(target_categories, base_categories)

        assert result == []

    def test_empty_old(self):
        """Empty base_categories list should return empty result."""
        result = find_missing_categories([create_category_link_from_str("[[Category:Cat1]]")], [])

        assert result == []

    def test_empty_new(self):
        """Empty target_categories list should return all base_categories categories."""
        base_categories = [
            create_category_link_from_str("[[Category:Cat1]]"),
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
        # نستخدم create_category_link_from_str مباشر لضمان التحكم في البيانات
        base_categories = [create_category_link_from_str("[[Category:Our_World_in_Data_graphs_of_Afghanistan]]")]
        target_categories = []  # النص الجديد لا يحتوي عليه

        result = find_missing_categories(target_categories, base_categories)

        assert len(result) == 1
        assert result[0].target == "Category:Our World in Data graphs of Afghanistan"

    def test_old_has_special_new_present(self):
        """If both have the same category with underscore, it should not be missing."""
        base_categories = [create_category_link_from_str("[[Category:Cyber Security]]")]
        target_categories = [create_category_link_from_str("[[Category:Cyber_Security]]")]  # نفس التصنيف

        result = find_missing_categories(target_categories, base_categories)
        assert len(result) == 0

    def test_special_chars_case_insensitive_matching(self):
        """Ensure matching works correctly even if case varies (standard wiki behavior)."""
        # في ويكي، القوائم عادية الحروف غالباً لكن الترميز مهم.
        # هنا نتحقق من أن الشرطات السفلية لا تكسر المقارنة إذا كانت الأسماء متطابقة.
        base_categories = [create_category_link_from_str("[[Category:test_Data]]")]
        target_categories = [create_category_link_from_str("[[Category:Test_Data]]")]  # اختلاف في حالة الحروف

        # ملاحظة: سلوك wtp يعتمد على الإعدادات، لكن المنطق هنا هو التأكد من عدم الإضافة المزدوجة
        result = find_missing_categories(target_categories, base_categories)
        # عادة لا يتم اعتبارها مفقودة إذا كانت متطابقة في المعنى، ولكن حسب منطق الكود الحالي:
        # يجب أن يعود راسياً (0) لأن النص تم ترميزه أو مقارنته كنصوص.
        assert len(result) == 0

    def test_multiple_missing_with_underscores(self):
        """Missing multiple categories with underscores."""
        base_categories = [
            create_category_link_from_str("[[Category:Afghanistan]]"),
            create_category_link_from_str("[[Category:Economy_Data]]")
        ]
        target_categories = [
            create_category_link_from_str("[[Category:Afghanistan]]")
            # Economy_Data مفقودة
        ]

        result = find_missing_categories(target_categories, base_categories)
        assert len(result) == 1
        assert "Economy" in result[0].target
