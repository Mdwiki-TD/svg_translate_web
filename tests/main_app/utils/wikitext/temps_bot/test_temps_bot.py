# test_wikitext_processing.py
# -*- coding: utf-8 -*-

"""
Pytest test suite for:
- get_titles
- get_titles_from_wikilinks

"""

from src.main_app.utils.wikitext.temps_bot import get_titles, get_titles_from_wikilinks


def test_get_titles_from_wikilinks(sample_from_prompt: str):
    """Returns empty list when owidslidersrcs contains no File entries."""
    titles = get_titles(sample_from_prompt)

    titles_new = get_titles_from_wikilinks(sample_from_prompt)

    assert "Health-expenditure-government-expenditure,World,2022 (cropped).svg" not in titles
    assert "Health-expenditure-government-expenditure,World,2022 (cropped).svg" in titles_new
