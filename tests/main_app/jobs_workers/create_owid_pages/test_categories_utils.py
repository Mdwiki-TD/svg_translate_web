"""
Unit tests for create_owid_pages/categoriez_extract.py module.
"""

from __future__ import annotations

import pytest
from wikitextparser import WikiLink

from src.main_app.jobs_workers.create_owid_pages.categories_utils import (
    _extract_categories,
    extend_categories,
)


class TestExtractCategories:
    def test_extract_categories(self):
        text = """
        [[Category:Category1]]
        """
        categories = _extract_categories(text)
        assert categories[0].string == WikiLink('[[Category:Category1]]').string


class TestExtendCategories:
    def test_extend_categories(self):
        categories = ["Category1"]
        extended_categories = extend_categories(categories)
        assert extended_categories == ["Category1", "Category1-2", "Category1-3"]
