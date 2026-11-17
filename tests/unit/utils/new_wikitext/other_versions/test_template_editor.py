"""Tests for the generic, template-agnostic :class:`TemplateEditor`."""

from __future__ import annotations

import pytest
import wikitextparser as wtp
from src.main_app.utils.new_wikitext.template_editor import TemplateEditor


@pytest.fixture
def editor() -> TemplateEditor:
    return TemplateEditor()


@pytest.fixture
def strict_editor() -> TemplateEditor:
    """Editor whose value comparison is case sensitive."""
    return TemplateEditor(case_insensitive=False)


# -------------------------------------------------------------------- #
# Construction and helpers
# -------------------------------------------------------------------- #


class TestConstruction:
    def test_default_is_case_insensitive(self, editor: TemplateEditor) -> None:
        assert editor.case_insensitive is True

    def test_case_sensitivity_can_be_disabled(self, strict_editor: TemplateEditor) -> None:
        assert strict_editor.case_insensitive is False


class TestNormName:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Svg lang", "svg lang"),
            ("  Svg_Lang  ", "svg lang"),
            ("SVG_LANG", "svg lang"),
            ("other_versions", "other versions"),
            ("", ""),
        ],
    )
    def test_normalization(self, raw: str, expected: str) -> None:
        assert TemplateEditor.norm_name(raw) == expected

    def test_is_usable_without_an_instance(self) -> None:
        assert TemplateEditor.norm_name("A_B") == "a b"


class TestFind:
    def test_finds_template_by_exact_name(self, editor: TemplateEditor) -> None:
        tpl = editor.find(wtp.parse("{{Svg lang|ar}}"), "Svg lang")
        assert tpl is not None
        assert tpl.name.strip() == "Svg lang"

    @pytest.mark.parametrize("name", ["svg lang", "SVG LANG", "Svg_lang", " Svg lang "])
    def test_name_matching_ignores_case_underscore_and_spaces(self, editor: TemplateEditor, name: str) -> None:
        assert editor.find(wtp.parse("{{Svg lang|ar}}"), name) is not None

    def test_returns_none_when_missing(self, editor: TemplateEditor) -> None:
        assert editor.find(wtp.parse("{{Other|ar}}"), "Svg lang") is None

    def test_returns_none_for_plain_text(self, editor: TemplateEditor) -> None:
        assert editor.find(wtp.parse("just text"), "Svg lang") is None

    def test_returns_the_first_match(self, editor: TemplateEditor) -> None:
        tpl = editor.find(wtp.parse("{{Svg lang|ar}} {{Svg lang|de}}"), "Svg lang")
        assert tpl is not None
        assert tpl.string == "{{Svg lang|ar}}"

    def test_finds_nested_templates(self, editor: TemplateEditor) -> None:
        parsed = wtp.parse("{{Information|other versions={{Svg lang|ar}}}}")
        assert editor.find(parsed, "Svg lang") is not None


# -------------------------------------------------------------------- #
# merge_positional
# -------------------------------------------------------------------- #


class TestMergePositionalCreate:
    """The template does not exist in the text yet."""

