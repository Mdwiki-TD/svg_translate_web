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


class TestExtractCategoriesWithSpecialChars:
    def test_extract_category_with_underscore(self):
        """Should extract categories containing underscores correctly."""
        text = "[[Category:Our_World_in_Data_graphs_of_Afghanistan]]"
        categories = extract_categories(text)
        assert len(categories) == 1
        # التحقق من أن الهدف يحافظ على النص الأصلي (مع الترميز إذا لزم الأمر أو بدون حسب سلوك الويكي)
        assert categories[0].target == "Category:Our_World_in_Data_graphs_of_Afghanistan"

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
            "Category:Data_Graphics",
            "Category:Graph_of_Cities"
        ]
        assert targets == expected_targets

    def test_extract_mixed_normal_and_special_categories(self):
        """Should mix normal and special categories."""
        text = "[[Category:Cyber_Security]] [[Category:Society]] [[Category:Night_Owl]]"
        categories = extract_categories(text)
        assert len(categories) == 3

        targets = [c.target for c in categories]
        assert "Category:Cyber_Security" in targets
        assert "Category:Society" in targets
        assert "Category:Night_Owl" in targets


class TestFindMissingCategoriesWithSpecialChars:
    def test_old_has_special_new_missing(self):
        """Old text has a category with underscore, new text is missing it."""
        # نستخدم WikiLink مباشر لضمان التحكم في البيانات
        base_categories = [WikiLink("[[Category:Our_World_in_Data_graphs_of_Afghanistan]]")]
        target_categories = []  # النص الجديد لا يحتوي عليه

        result = find_missing_categories(target_categories, base_categories)

        assert len(result) == 1
        assert result[0].target == "Category:Our_World_in_Data_graphs_of_Afghanistan"

    def test_old_has_special_new_present(self):
        """If both have the same category with underscore, it should not be missing."""
        base_categories = [WikiLink("[[Category:Cyber_Security]]")]
        target_categories = [WikiLink("[[Category:Cyber_Security]]")]  # نفس التصنيف

        result = find_missing_categories(target_categories, base_categories)
        assert len(result) == 0

    def test_special_chars_case_insensitive_matching(self):
        """Ensure matching works correctly even if case varies (standard wiki behavior)."""
        # في ويكي، القوائم عادية الحروف غالباً لكن الترميز مهم.
        # هنا نتحقق من أن الشرطات السفلية لا تكسر المقارنة إذا كانت الأسماء متطابقة.
        base_categories = [WikiLink("[[Category:Test_Data]]")]
        target_categories = [WikiLink("[[Category:TEST_DATA]]")]  # اختلاف في حالة الحروف

        # ملاحظة: سلوك wtp يعتمد على الإعدادات، لكن المنطق هنا هو التأكد من عدم الإضافة المزدوجة
        result = find_missing_categories(target_categories, base_categories)
        # عادة لا يتم اعتبارها مفقودة إذا كانت متطابقة في المعنى، ولكن حسب منطق الكود الحالي:
        # يجب أن يعود راسياً (0) لأن النص تم ترميزه أو مقارنته كنصوص.
        assert len(result) == 0

    def test_multiple_missing_with_underscores(self):
        """Missing multiple categories with underscores."""
        base_categories = [
            WikiLink("[[Category:Afghanistan]]"),
            WikiLink("[[Category:Economy_Data]]")
        ]
        target_categories = [
            WikiLink("[[Category:Afghanistan]]")
            # Economy_Data مفقودة
        ]

        result = find_missing_categories(target_categories, base_categories)
        assert len(result) == 1
        assert "Economy" in result[0].target


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

        # يجب أن تظهر مرة واحدة فقط
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
        new_text = ""
