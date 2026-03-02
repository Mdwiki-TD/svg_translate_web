# test_wikitext_processing.py
# -*- coding: utf-8 -*-

"""
Pytest test suite for:
- get_files_list
"""

import pytest

from src.main_app.utils.wikitext.temps_bot import get_files_list


# ---------- Tests for get_files_list (integration) ----------


def test_get_files_list_prefers_svglanguages(sample_with_both_titles, sample_multiple_owidslidersrcs):
    """get_files_list should return (main_title, titles) preferring SVGLanguages."""
    main, titles = get_files_list(
        sample_with_both_titles + "\n" + sample_multiple_owidslidersrcs, filter_duplicates=False
    )
    assert main == "some_main_title,World,2010.svg".replace("_", " ")
    assert len(titles) == 4
    assert "Gamma, 2002 to 2003, CCC.svg" in titles


def test_get_files_list_falls_back_to_translate(sample_from_prompt):
    """If no SVGLanguages then fallback to Translate regex."""
    main, titles = get_files_list(sample_from_prompt)
    assert main == "File:health-expenditure-government-expenditure,World,2000.svg"
    assert "health-expenditure-government-expenditure, 2000 to 2022, YEM.svg" in titles
    assert len(titles) == 9


def test_get_files_list_no_titles_no_main(sample_without_titles):
    """When neither titles nor main title exist."""
    main, titles = get_files_list(sample_without_titles)
    assert main is None
    assert titles == []
