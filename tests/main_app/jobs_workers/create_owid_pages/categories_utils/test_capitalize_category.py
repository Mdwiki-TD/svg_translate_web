"""
Unit tests for create_owid_pages/categoriez_extract.py module.
"""

from __future__ import annotations

from src.main_app.jobs_workers.create_owid_pages.categories_utils import (
    capitalize_category,
)


class TestCapitalizeCategory:
    def test_capitalize_category(self):
        """Should capitalize the first letter of the category name."""
        capitalized_category = capitalize_category("cateGory:catTest")
        assert capitalized_category == "CateGory:CatTest"

    def test_simple_category(self):
        assert capitalize_category("fruit:apple") == "Fruit:Apple"

    def test_category_with_spaces(self):
        assert capitalize_category(" fruit : apple ") == "Fruit : apple"

    def test_category_with_special_chars(self):
        assert capitalize_category("\tfruit\t:\tapple\t") == "Fruit\t:\tapple"

    def test_single_part_category(self):
        assert capitalize_category("fruit") == "fruit"

    def test_empty_parts(self):
        assert capitalize_category(":apple") == ":Apple"
        assert capitalize_category("fruit:") == "Fruit:"

    def test_empty_string(self):
        assert capitalize_category("") == ""

    def test_multiple_colons(self):
        assert capitalize_category("fruit:apple:banana") == "Fruit:Apple:banana"

    def test_single_character_parts(self):
        assert capitalize_category("f:a") == "F:A"

    def test_uppercase_input(self):
        assert capitalize_category("FRUIT:APPLE") == "FRUIT:APPLE"

    def test_mixed_case_input(self):
        assert capitalize_category("fRuIt:aPpLe") == "FRuIt:APpLe"

    def test_numeric_parts(self):
        assert capitalize_category("1:2") == "1:2"

    def test_unicode_chars(self):
        assert capitalize_category("ápple:örange") == "Ápple:Örange"
