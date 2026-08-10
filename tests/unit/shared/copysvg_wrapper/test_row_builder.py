"""Tests for the interactive translate row_builder module."""

from __future__ import annotations

import pytest

from src.main_app.shared.copysvg_wrapper.mapping import ExtractorData
from src.main_app.shared.copysvg_wrapper.row_builder import (
    TranslateRow,
    mapping_from_rows,
    rows_for_language,
    summary_from_rows,
)


class TestRowsForLanguage:
    """Tests for rows_for_language()."""

    def test_empty_mapping_returns_empty_rows(self):
        mapping = ExtractorData()
        rows = rows_for_language(mapping, "ar")
        assert rows == []

    def test_existing_translation_populated(self):
        mapping = ExtractorData(
            new={"Hello": {"ar": "مرحبا", "fr": "Bonjour"}}
        )
        rows = rows_for_language(mapping, "ar")

        assert len(rows) == 1
        assert rows[0].source == "Hello"
        assert rows[0].current == "مرحبا"
        assert rows[0].status == "existing"
        assert rows[0].row_index == 0

    def test_missing_translation_shows_empty(self):
        mapping = ExtractorData(
            new={"Hello": {"fr": "Bonjour"}}
        )
        rows = rows_for_language(mapping, "ar")

        assert len(rows) == 1
        assert rows[0].source == "Hello"
        assert rows[0].current == ""
        assert rows[0].status == "missing"

    def test_multiple_sources(self):
        mapping = ExtractorData(
            new={
                "Hello": {"ar": "مرحبا"},
                "Goodbye": {"ar": "مع السلامة"},
                "Thanks": {"fr": "Merci"},
            }
        )
        rows = rows_for_language(mapping, "ar")

        assert len(rows) == 3
        assert rows[0].status == "existing"
        assert rows[1].status == "existing"
        assert rows[2].status == "missing"

    def test_case_insensitive_language_match(self):
        mapping = ExtractorData(
            new={"Hello": {"AR": "مرحبا"}}
        )
        rows = rows_for_language(mapping, "ar", case_insensitive=True)

        assert len(rows) == 1
        assert rows[0].current == "مرحبا"
        assert rows[0].status == "existing"

    def test_case_sensitive_language_no_match(self):
        mapping = ExtractorData(
            new={"Hello": {"AR": "مرحبا"}}
        )
        rows = rows_for_language(mapping, "ar", case_insensitive=False)

        assert len(rows) == 1
        assert rows[0].current == ""
        assert rows[0].status == "missing"

    def test_row_index_increments(self):
        mapping = ExtractorData(
            new={
                "A": {"ar": "a"},
                "B": {"ar": "b"},
                "C": {"ar": "c"},
            }
        )
        rows = rows_for_language(mapping, "ar")

        assert [r.row_index for r in rows] == [0, 1, 2]

    def test_title_new_section_not_included(self):
        """rows_for_language only iterates .new, not .title_new."""
        mapping = ExtractorData(
            new={"Hello": {"ar": "مرحبا"}},
            title_new={"Music in {year}": {"ar": "الموسيقى في {year}"}},
        )
        rows = rows_for_language(mapping, "ar")

        # Only the "new" section is included
        assert len(rows) == 1
        assert rows[0].source == "Hello"

    def test_non_dict_trans_value_skipped(self):
        """If a translation value is not a dict, it's treated as missing."""
        mapping = ExtractorData(new={"Hello": "not-a-dict"})  # type: ignore[arg-type]
        rows = rows_for_language(mapping, "ar")

        assert len(rows) == 1
        assert rows[0].current == ""
        assert rows[0].status == "missing"


class TestMappingFromRows:
    """Tests for mapping_from_rows()."""

    def test_empty_rows_returns_empty_mapping(self):
        result = mapping_from_rows([], "ar")
        assert result == {"new": {}}

    def test_single_row(self):
        rows = [{"source": "Hello", "target": "مرحبا"}]
        result = mapping_from_rows(rows, "ar")

        assert result == {"new": {"Hello": {"ar": "مرحبا"}}}

    def test_multiple_rows(self):
        rows = [
            {"source": "Hello", "target": "مرحبا"},
            {"source": "Goodbye", "target": "مع السلامة"},
        ]
        result = mapping_from_rows(rows, "ar")

        assert result["new"]["Hello"]["ar"] == "مرحبا"
        assert result["new"]["Goodbye"]["ar"] == "مع السلامة"

    def test_empty_target_skipped(self):
        rows = [
            {"source": "Hello", "target": "مرحبا"},
            {"source": "Goodbye", "target": ""},
        ]
        result = mapping_from_rows(rows, "ar")

        assert "Hello" in result["new"]
        assert "Goodbye" not in result["new"]

    def test_whitespace_only_target_skipped(self):
        rows = [{"source": "Hello", "target": "   "}]
        result = mapping_from_rows(rows, "ar")
        assert result == {"new": {}}

    def test_empty_source_skipped(self):
        rows = [{"source": "", "target": "مرحبا"}]
        result = mapping_from_rows(rows, "ar")
        assert result == {"new": {}}

    def test_whitespace_stripped(self):
        rows = [{"source": "  Hello  ", "target": "  مرحبا  "}]
        result = mapping_from_rows(rows, "ar")
        assert result["new"]["Hello"]["ar"] == "مرحبا"

    def test_roundtrip_extract_to_form_to_inject(self):
        """Full roundtrip: extract → rows → form edit → mapping."""
        original = ExtractorData(
            new={
                "Hello": {"fr": "Bonjour"},
                "Goodbye": {"fr": "Au revoir"},
            }
        )

        # Extract rows for Arabic
        rows = rows_for_language(original, "ar")
        assert all(r.status == "missing" for r in rows)

        # Simulate user filling in translations
        form_rows = [
            {"source": r.source, "target": f"AR_{r.source}"}
            for r in rows
        ]

        # Build mapping for injection
        result = mapping_from_rows(form_rows, "ar")
        assert result["new"]["Hello"]["ar"] == "AR_Hello"
        assert result["new"]["Goodbye"]["ar"] == "AR_Goodbye"


class TestTranslateRow:
    """Tests for TranslateRow dataclass."""

    def test_to_dict(self):
        row = TranslateRow(source="Hello", current="مرحبا", status="existing", row_index=0)
        d = row.to_dict()

        assert d == {
            "source": "Hello",
            "current": "مرحبا",
            "status": "existing",
            "row_index": 0,
        }


class TestSummaryFromRows:
    """Tests for summary_from_rows()."""

    def test_empty_rows(self):
        assert summary_from_rows([]) == {"total": 0, "existing": 0, "missing": 0}

    def test_all_existing(self):
        rows = [
            TranslateRow(source="A", current="a", status="existing"),
            TranslateRow(source="B", current="b", status="existing"),
        ]
        assert summary_from_rows(rows) == {"total": 2, "existing": 2, "missing": 0}

    def test_all_missing(self):
        rows = [
            TranslateRow(source="A", current="", status="missing"),
            TranslateRow(source="B", current="", status="missing"),
            TranslateRow(source="C", current="", status="missing"),
        ]
        assert summary_from_rows(rows) == {"total": 3, "existing": 0, "missing": 3}

    def test_mixed(self):
        rows = [
            TranslateRow(source="A", current="a", status="existing"),
            TranslateRow(source="B", current="", status="missing"),
            TranslateRow(source="C", current="c", status="existing"),
        ]
        assert summary_from_rows(rows) == {"total": 3, "existing": 2, "missing": 1}
