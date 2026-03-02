"""Tests for the wikitext.before_mothods module."""

from __future__ import annotations

from src.main_app.utils.wikitext.before_mothods import insert_before_methods


class TestInsertBeforeMethods:
    """Tests for the insert_before_methods function."""

    def test_insert_before_license_header(self):
        """Test inserting before the license header."""
        text_input = """== {{int:license-header}} ==
{{Information
|description={{en|1=Some description}}
|author = Test Author
}}"""
        text_output = """
== New Section ==

== {{int:license-header}} ==
{{Information
|description={{en|1=Some description}}
|author = Test Author
}}"""
        result = insert_before_methods(text_input, "== New Section ==")
        assert result == text_output
