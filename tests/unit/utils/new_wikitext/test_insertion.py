from __future__ import annotations

from src.main_app.utils.new_wikitext.insertion import BeforeMarkerInserter


class TestInsertBeforeMethods:
    """Tests for the insert_before_methods function."""

    def test_insert_before_license_header(self):
        """Test inserting before the license header."""
        text_input = """== {{int:license-header}} ==\n{{Information\n|description={{en|1=Some description}}\n|author = Test Author\n}}"""
        text_output = """\n== New Section ==\n\n== {{int:license-header}} ==\n{{Information\n|description={{en|1=Some description}}\n|author = Test Author\n}}"""
        result = BeforeMarkerInserter.insert_before_methods(text_input, "== New Section ==")
        assert result == text_output


class TestBeforeMarkerInserterAddBefore:
    """Tests for ``BeforeMarkerInserter.add_before``."""

    def test_inserts_before_match(self):
        result = BeforeMarkerInserter.add_before("a\n[[Category:X]]", "NEW", r"\[\[category:")
        assert result == "a\nNEW\n\n[[Category:X]]"

    def test_returns_text_when_no_match(self):
        assert BeforeMarkerInserter.add_before("abc", "NEW", "zzz") == "abc"


class TestBeforeMarkerInserterInsertBeforeMethods:
    """Tests for ``BeforeMarkerInserter.insert_before_methods``."""

    def test_prefers_license_header(self):
        text = "a\n== {{int:license-header}} ==\n[[Category:X]]"
        result = BeforeMarkerInserter.insert_before_methods(text, "NEW")
        assert result.index("NEW") < result.index("license-header")

    def test_falls_back_to_category(self):
        result = BeforeMarkerInserter.insert_before_methods("a\n[[Category:X]]", "NEW")
        assert result == "a\nNEW\n\n[[Category:X]]"

    def test_returns_text_when_no_marker(self):
        assert BeforeMarkerInserter.insert_before_methods("plain", "NEW") == "plain"
