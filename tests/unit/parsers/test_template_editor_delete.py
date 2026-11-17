"""Tests for ``TemplateEditor.delete_values``."""

from __future__ import annotations

import pytest
import wikitextparser as wtp
from src.main_app.parsers.template_editor import TemplateEditor

SVG_LANG_TEMPLATE = "Svg lang"


@pytest.fixture
def editor() -> TemplateEditor:
    return TemplateEditor()


def svg_lang_values(text: str) -> list[str]:
    """Return the positional values of the first {{Svg lang}} template."""
    for tpl in wtp.parse(text).templates:
        if tpl.name.replace("_", " ").strip().lower() == "svg lang":
            return [a.value.strip() for a in tpl.arguments]
    return []


# -------------------------------------------------------------------- #
# delete_values
# -------------------------------------------------------------------- #


class TestDeleteValuesMore:
    def test_removes_matching_values(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|ar|de|fr}}", SVG_LANG_TEMPLATE, ["de"])
        assert "{{Svg lang|ar|fr}}" in result

    def test_case_insensitive(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|ar|de}}", SVG_LANG_TEMPLATE, ["DE"])
        assert "{{Svg lang|ar}}" in result

    def test_other_templates_are_untouched(self, editor: TemplateEditor) -> None:
        text = "{{Extracted from|1=ar}}\n{{Svg lang|ar|de}}"
        result = editor.delete_values(text, SVG_LANG_TEMPLATE, ["ar"])
        assert "{{Extracted from|1=ar}}\n{{Svg lang|de}}" in result

    def test_no_match_returns_text_unchanged(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar}}"
        assert editor.delete_values(text, SVG_LANG_TEMPLATE, ["xx"]) == text

    @pytest.mark.parametrize("values", [[], [""]])
    def test_empty_values_return_text_unchanged(self, editor: TemplateEditor, values: list[str]) -> None:
        text = "{{Svg lang|ar}}"
        assert editor.delete_values(text, SVG_LANG_TEMPLATE, values) == text

    def test_missing_main_template_returns_text_unchanged(self, editor: TemplateEditor) -> None:
        text = "{{svg_lang_test|ar}}"
        assert editor.delete_values(text, SVG_LANG_TEMPLATE, ["ar"]) == text

    def test_with_underscore(self, editor: TemplateEditor) -> None:
        text = "{{ svg_lang |1=ar}}"
        assert editor.delete_values(text, SVG_LANG_TEMPLATE, ["ar"]) == "{{ svg_lang }}"

    def test_only_the_param_is_searched(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar}}" + "\n{{Svg lang|ar}}"
        result = editor.delete_values(text, SVG_LANG_TEMPLATE, ["ar"])
        assert "{{Svg lang}}" in result
        assert result.endswith("\n{{Svg lang|ar}}")


class TestDeleteValues:
    # ---------------------------------------------------------------- #
    # Nothing to do
    # ---------------------------------------------------------------- #

    def test_returns_text_unchanged_when_no_svg_lang_template(self, editor: TemplateEditor) -> None:
        text = "{{Information\n|other versions={{Extracted from|1=File.svg}}\n}}"
        assert editor.delete_values(text, SVG_LANG_TEMPLATE, ["ar"]) == text

    def test_returns_text_unchanged_for_plain_text(self, editor: TemplateEditor) -> None:
        text = "just some text without templates"
        assert editor.delete_values(text, SVG_LANG_TEMPLATE, ["ar"]) == text

    def test_returns_text_unchanged_for_empty_text(self, editor: TemplateEditor) -> None:
        assert editor.delete_values("", SVG_LANG_TEMPLATE, ["ar"]) == ""

    def test_returns_text_unchanged_when_delete_values_is_empty(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar|de|fr}}"
        assert editor.delete_values(text, SVG_LANG_TEMPLATE, []) == text

    def test_returns_text_unchanged_when_value_not_present(self, editor: TemplateEditor):
        text = "{{Svg lang|ar|de|fr}}"
        assert editor.delete_values(text, SVG_LANG_TEMPLATE, ["es"]) == text

    # ---------------------------------------------------------------- #
    # Deleting values
    # ---------------------------------------------------------------- #

    def test_deletes_single_value(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|ar|de|fr}}", SVG_LANG_TEMPLATE, ["de"])
        assert svg_lang_values(result) == ["ar", "fr"]

    def test_deletes_first_value(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|ar|de|fr}}", SVG_LANG_TEMPLATE, ["ar"])
        assert svg_lang_values(result) == ["de", "fr"]

    def test_deletes_last_value(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|ar|de|fr}}", SVG_LANG_TEMPLATE, ["fr"])
        assert svg_lang_values(result) == ["ar", "de"]

    def test_deletes_multiple_values(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|ar|de|fr|es}}", SVG_LANG_TEMPLATE, ["de", "es"])
        assert svg_lang_values(result) == ["ar", "fr"]

    def test_deletes_adjacent_values(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|ar|de|fr|es}}", SVG_LANG_TEMPLATE, ["de", "fr"])
        assert svg_lang_values(result) == ["ar", "es"]

    def test_deletes_all_values(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|ar|de}}", SVG_LANG_TEMPLATE, ["ar", "de"])
        assert svg_lang_values(result) == []

    def test_ignores_unknown_values_mixed_with_known_ones(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|ar|de|fr}}", SVG_LANG_TEMPLATE, ["xx", "de"])
        assert svg_lang_values(result) == ["ar", "fr"]

    # ---------------------------------------------------------------- #
    # Matching rules
    # ---------------------------------------------------------------- #

    def test_match_is_case_insensitive_on_template_values(self, editor: TemplateEditor) -> None:
        # delete_values are expected to be lowercase (see add_svg_langs).
        result = editor.delete_values("{{Svg lang|AR|De|fr}}", SVG_LANG_TEMPLATE, ["ar", "de"])
        assert svg_lang_values(result) == ["fr"]

    def test_match_ignores_whitespace_around_values(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang| ar | de |fr}}", SVG_LANG_TEMPLATE, ["ar", "de"])
        assert svg_lang_values(result) == ["fr"]

    @pytest.mark.parametrize(
        "template_name",
        [SVG_LANG_TEMPLATE, "svg lang", "Svg_lang", "Svg Lang", " Svg lang "],
    )
    def test_template_name_matching_is_normalized(self, editor, template_name):
        text = "{{" + template_name + "|ar|de}}"
        result = editor.delete_values(text, SVG_LANG_TEMPLATE, ["ar"])
        assert svg_lang_values(result) == ["de"]

    def test_does_not_delete_partial_matches(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|ar|ara|de}}", SVG_LANG_TEMPLATE, ["ar"])
        assert svg_lang_values(result) == ["ara", "de"]

    # ---------------------------------------------------------------- #
    # Surrounding content
    # ---------------------------------------------------------------- #

    def test_other_templates_are_untouched(self, editor: TemplateEditor) -> None:
        text = "{{Extracted from|1=File.svg}}\n{{Svg lang|ar|de}}"
        result = editor.delete_values(text, SVG_LANG_TEMPLATE, ["ar"])
        assert "{{Extracted from|1=File.svg}}" in result
        assert svg_lang_values(result) == ["de"]

    def test_other_templates_with_same_values_are_untouched(self, editor: TemplateEditor) -> None:
        text = "{{Other|ar|de}}\n{{Svg lang|ar|de}}"
        result = editor.delete_values(text, SVG_LANG_TEMPLATE, ["ar"])
        assert "{{Other|ar|de}}" in result
        assert svg_lang_values(result) == ["de"]

    def test_text_outside_template_is_preserved(self, editor: TemplateEditor) -> None:
        text = "before {{Svg lang|ar|de}} after"
        result = editor.delete_values(text, SVG_LANG_TEMPLATE, ["ar"])
        assert result.startswith("before ")
        assert result.endswith(" after")

    def test_deletes_inside_information_other_versions(self, editor: TemplateEditor) -> None:
        text = (
            "== {{int:filedesc}} ==\n"
            "{{Information\n"
            "|description=Test\n"
            "|other versions={{Svg lang|ar|de|fr}}\n"
            "|source=Own work\n"
            "}}"
        )
        result = editor.delete_values(text, SVG_LANG_TEMPLATE, ["de"])
        assert svg_lang_values(result) == ["ar", "fr"]
        assert "|description=Test" in result
        assert "|source=Own work" in result

    def test_result_is_still_valid_template(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|ar|de|fr}}", SVG_LANG_TEMPLATE, ["de"])

        has = editor.find(wtp.parse(result), "svg lang")
        assert has is not None

        assert result.startswith("{{") and result.endswith("}}")

    # ---------------------------------------------------------------- #
    # Idempotency
    # ---------------------------------------------------------------- #

    def test_is_idempotent(self, editor: TemplateEditor):
        once = editor.delete_values("{{Svg lang|ar|de|fr}}", SVG_LANG_TEMPLATE, ["de"])
        twice = editor.delete_values(once, SVG_LANG_TEMPLATE, ["de"])
        assert once == twice

    def test_delete_values_removes_codes_directly(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|dl=en|ar|de}}"
        result = editor.delete_values(text, SVG_LANG_TEMPLATE, ["ar"])
        assert "{{Svg lang|dl=en|de}}" in result

    def test_delete_params_targets_svg_lang(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar|de}}\n{{Other|ar}}"
        result = editor.delete_values(text, SVG_LANG_TEMPLATE, ["ar"])
        assert "{{Svg lang|de}}" in result
        assert "{{Other|ar}}" in result

    def test_delete_params_works_on_the_whole_text_without_main_template(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar|de|fr}}"
        assert editor.delete_values(text, SVG_LANG_TEMPLATE, ["de"]) == "{{Svg lang|ar|fr}}"

    def test_delete_params_without_svg_lang_returns_text_unchanged(self, editor: TemplateEditor) -> None:
        text = "{{Other|ar}}"
        assert editor.delete_values(text, SVG_LANG_TEMPLATE, ["ar"]) == text


class TestDeleteValuesWithOnlyFirstOption:
    def test_delete_in_only_first_template(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar|de}}\n{{Svg lang|ar|de}}"
        result = editor.delete_values(text, SVG_LANG_TEMPLATE, ["de"], only_first=True)
        assert result == "{{Svg lang|ar}}\n{{Svg lang|ar|de}}"

    def test_delete_in_all_templates(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar|de}}\n{{Svg lang|ar|de}}"
        result = editor.delete_values(text, SVG_LANG_TEMPLATE, ["de"], only_first=False)
        assert result == "{{Svg lang|ar}}\n{{Svg lang|ar}}"
