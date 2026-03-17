"""
Unit tests for create_owid_pages/categoriez_extract.py module.
"""

from __future__ import annotations

from src.main_app.jobs_workers.create_owid_pages.categories_utils import (
    extract_categories,
    find_missing_categories,
    merge_categories,
)


def test_full_pipeline() -> None:
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
