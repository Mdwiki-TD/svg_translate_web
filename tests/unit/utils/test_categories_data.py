"""Tests for src/main_app/utils/categories_data.py."""

from __future__ import annotations

from src.main_app.utils.categories_data import LANG_CODE_CATEGORY_MAP  # noqa: F401
from src.main_app.utils.categories_data import lang_code_category


class TestLangCodeCategory:
    def test_known_code(self):
        assert lang_code_category("en") == "English-language SVG"
        assert lang_code_category("fr") == "French-language SVG"
        assert lang_code_category("ar") == "Arabic-language SVG"

    def test_unknown_code(self):
        assert lang_code_category("xyz") is None

    def test_empty_string(self):
        assert lang_code_category("") is None
