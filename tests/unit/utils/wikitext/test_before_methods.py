"""Tests for the wikitext.before_mothods module."""

from __future__ import annotations

from src.main_app.utils.wikitext.before_methods import insert_before_methods


class TestInsertBeforeMethods:
    """Tests for the insert_before_methods function."""

    def test_insert_before_license_header(self):
        """Test inserting before the license header."""
        text_input = """== {{int:license-header}} ==\n{{Information\n|description={{en|1=Some description}}\n|author = Test Author\n}}"""
        text_output = """\n== New Section ==\n\n== {{int:license-header}} ==\n{{Information\n|description={{en|1=Some description}}\n|author = Test Author\n}}"""
        result = insert_before_methods(text_input, "== New Section ==")
        assert result == text_output
