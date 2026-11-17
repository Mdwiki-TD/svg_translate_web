"""Tests for the generic, template-agnostic :class:`TemplateEditor`."""

from __future__ import annotations

import pytest
import wikitextparser as wtp
from src.main_app.parsers.template_editor import TemplateEditor


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

    def test_creates_template_in_empty_text(self, editor: TemplateEditor) -> None:
        assert editor.merge_positional("", "Svg lang", ["ar", "de"]) == "{{Svg lang|ar|de}}"

    def test_appends_after_existing_text_on_a_new_line(self, editor: TemplateEditor) -> None:
        result = editor.merge_positional("{{Extracted from|1=A.svg}}", "Svg lang", ["ar"])
        assert result == "{{Extracted from|1=A.svg}}\n{{Svg lang|ar}}"

    def test_uses_the_given_template_name_spelling(self, editor: TemplateEditor) -> None:
        assert editor.merge_positional("", "svg_lang", ["ar"]) == "{{svg_lang|ar}}"

    def test_sorts_new_template_when_requested(self, editor: TemplateEditor) -> None:
        assert editor.merge_positional("", "Svg lang", ["fr", "ar", "de"], sort=True) == "{{Svg lang|ar|de|fr}}"

    def test_keeps_insertion_order_by_default(self, editor: TemplateEditor) -> None:
        assert editor.merge_positional("", "Svg lang", ["fr", "ar", "de"]) == "{{Svg lang|fr|ar|de}}"

    def test_duplicates_in_input_are_collapsed_keeping_first_spelling(self, editor: TemplateEditor) -> None:
        assert editor.merge_positional("", "Svg lang", ["ar", "AR", "ar"]) == "{{Svg lang|ar}}"


class TestMergePositionalExisting:
    def test_appends_new_values_in_order(self, editor: TemplateEditor) -> None:
        assert editor.merge_positional("{{Svg lang|ar|de}}", "Svg lang", ["fr", "es"]) == "{{Svg lang|ar|de|fr|es}}"

    def test_only_missing_values_are_added(self, editor: TemplateEditor) -> None:
        assert editor.merge_positional("{{Svg lang|ar|de}}", "Svg lang", ["de", "fr"]) == "{{Svg lang|ar|de|fr}}"

    def test_does_not_create_a_second_template(self, editor: TemplateEditor) -> None:
        result = editor.merge_positional("{{Svg lang|ar}}", "Svg lang", ["de"])
        assert result.count("{{Svg lang") == 1

    def test_sort_applies_to_the_merged_list(self, editor: TemplateEditor) -> None:
        result = editor.merge_positional("{{Svg lang|fr|ar}}", "Svg lang", ["de"], sort=True)
        assert result == "{{Svg lang|ar|de|fr}}"

    def test_numbered_params_are_normalized_to_positional(self, editor: TemplateEditor) -> None:
        result = editor.merge_positional("{{Svg lang|1=ar|2=de}}", "Svg lang", ["fr"])
        assert result == "{{Svg lang|ar|de|fr}}"

    def test_named_params_are_kept_after_positional_ones(self, editor: TemplateEditor) -> None:
        result = editor.merge_positional("{{Svg lang|foo=bar|ar}}", "Svg lang", ["de"])
        assert result == "{{Svg lang|ar|de|foo=bar}}"

    def test_empty_positional_slots_are_dropped(self, editor: TemplateEditor) -> None:
        result = editor.merge_positional("{{Svg lang||ar}}", "Svg lang", ["de"])
        assert result == "{{Svg lang|ar|de}}"

    def test_template_name_spelling_in_text_is_preserved(self, editor: TemplateEditor) -> None:
        assert editor.merge_positional("{{svg lang|ar}}", "Svg lang", ["de"]) == "{{svg lang|ar|de}}"

    def test_underscore_in_template_name_is_matched(self, editor: TemplateEditor) -> None:
        assert editor.merge_positional("{{Svg_lang|ar}}", "Svg lang", ["de"]) == "{{Svg_lang|ar|de}}"

    def test_surrounding_text_is_preserved(self, editor: TemplateEditor) -> None:
        result = editor.merge_positional("before {{Svg lang|ar}} after", "Svg lang", ["de"])
        assert result == "before {{Svg lang|ar|de}} after"

    def test_only_the_first_matching_template_is_changed(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar}}\n{{Svg lang|de}}"
        assert editor.merge_positional(text, "Svg lang", ["fr"]) == "{{Svg lang|ar|fr}}\n{{Svg lang|de}}"

    def test_duplicates_already_in_the_template_are_collapsed_when_something_is_added(
        self, editor: TemplateEditor
    ) -> None:
        assert editor.merge_positional("{{Svg lang|ar|ar}}", "Svg lang", ["de"]) == "{{Svg lang|ar|de}}"

    def test_other_templates_in_the_text_are_untouched(self, editor: TemplateEditor) -> None:
        text = "{{Extracted from|1=A.svg}}\n{{Svg lang|ar}}"
        result = editor.merge_positional(text, "Svg lang", ["de"])
        assert result == "{{Extracted from|1=A.svg}}\n{{Svg lang|ar|de}}"


class TestMergePositionalNoChange:
    def test_nothing_new_returns_text_unchanged(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar|de}}"
        assert editor.merge_positional(text, "Svg lang", ["de"]) == text

    def test_existing_duplicates_alone_do_not_trigger_a_rewrite(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar|ar}}"
        assert editor.merge_positional(text, "Svg lang", ["ar"]) == text

    def test_case_insensitive_match_means_no_change(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar|de}}"
        assert editor.merge_positional(text, "Svg lang", ["AR", "De"]) == text

    def test_underscore_and_space_are_equivalent_in_values(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|a_b}}"
        assert editor.merge_positional(text, "Svg lang", ["a b"]) == text

    @pytest.mark.parametrize("values", [[], [""], ["  "], ["", "   "]])
    def test_blank_values_return_text_unchanged(self, editor: TemplateEditor, values: list[str]) -> None:
        text = "{{Svg lang|ar}}"
        assert editor.merge_positional(text, "Svg lang", values) == text

    @pytest.mark.parametrize("values", [[], [""], ["  "]])
    def test_blank_values_never_create_a_template(self, editor: TemplateEditor, values: list[str]) -> None:
        assert editor.merge_positional("", "Svg lang", values) == ""

    def test_is_idempotent(self, editor: TemplateEditor) -> None:
        once = editor.merge_positional("", "Svg lang", ["ar", "de"])
        assert editor.merge_positional(once, "Svg lang", ["ar", "de"]) == once


class TestMergePositionalCaseSensitivity:
    def test_strict_editor_treats_different_case_as_new_value(self, strict_editor: TemplateEditor) -> None:
        result = strict_editor.merge_positional("{{Svg lang|ar}}", "Svg lang", ["AR"])
        assert result == "{{Svg lang|ar|AR}}"

    def test_strict_editor_still_dedupes_identical_values(self, strict_editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar}}"
        assert strict_editor.merge_positional(text, "Svg lang", ["ar"]) == text

    def test_strict_editor_dedupes_input_by_exact_value(self, strict_editor: TemplateEditor) -> None:
        assert strict_editor.merge_positional("", "Svg lang", ["ar", "AR", "ar"]) == "{{Svg lang|ar|AR}}"


class TestMergePositionalValueCleaning:
    def test_values_are_stripped(self, editor: TemplateEditor) -> None:
        assert editor.merge_positional("", "Svg lang", ["  ar ", "\tde\n"]) == "{{Svg lang|ar|de}}"

    def test_blank_items_between_valid_values_are_skipped(self, editor: TemplateEditor) -> None:
        assert editor.merge_positional("", "Svg lang", ["ar", "", "  ", "de"]) == "{{Svg lang|ar|de}}"


# -------------------------------------------------------------------- #
# add_unique
# -------------------------------------------------------------------- #


class TestAddUnique:
    def test_creates_template_in_empty_text(self, editor: TemplateEditor) -> None:
        assert editor.add_unique("", "Extracted from", "A.svg") == "{{Extracted from|1=A.svg}}"

    def test_appends_on_a_new_line(self, editor: TemplateEditor) -> None:
        result = editor.add_unique("{{Svg lang|ar}}", "Extracted from", "A.svg")
        assert result == "{{Svg lang|ar}}\n{{Extracted from|1=A.svg}}"

    def test_skips_exact_duplicate(self, editor: TemplateEditor) -> None:
        text = "{{Extracted from|1=A.svg}}"
        assert editor.add_unique(text, "Extracted from", "A.svg") == text

    def test_duplicate_check_ignores_case(self, editor: TemplateEditor) -> None:
        text = "{{Extracted from|1=A.svg}}"
        assert editor.add_unique(text, "Extracted from", "a.SVG") == text

    def test_duplicate_check_treats_underscore_as_space(self, editor: TemplateEditor) -> None:
        text = "{{Extracted from|1=My_File.svg}}"
        assert editor.add_unique(text, "Extracted from", "My File.svg") == text

    def test_duplicate_check_ignores_template_name_case(self, editor: TemplateEditor) -> None:
        text = "{{extracted from|1=A.svg}}"
        assert editor.add_unique(text, "Extracted from", "A.svg") == text

    def test_positional_first_param_counts_as_duplicate(self, editor: TemplateEditor) -> None:
        text = "{{Extracted from|A.svg}}"
        assert editor.add_unique(text, "Extracted from", "A.svg") == text

    def test_different_value_adds_a_second_template(self, editor: TemplateEditor) -> None:
        result = editor.add_unique("{{Extracted from|1=A.svg}}", "Extracted from", "B.svg")
        assert result == "{{Extracted from|1=A.svg}}\n{{Extracted from|1=B.svg}}"

    def test_same_value_in_another_template_is_not_a_duplicate(self, editor: TemplateEditor) -> None:
        result = editor.add_unique("{{Derived from|1=A.svg}}", "Extracted from", "A.svg")
        assert result == "{{Derived from|1=A.svg}}\n{{Extracted from|1=A.svg}}"

    def test_strict_editor_treats_case_difference_as_new(self, strict_editor: TemplateEditor) -> None:
        result = strict_editor.add_unique("{{Extracted from|1=A.svg}}", "Extracted from", "a.svg")
        assert result == "{{Extracted from|1=A.svg}}\n{{Extracted from|1=a.svg}}"

    def test_is_idempotent(self, editor: TemplateEditor) -> None:
        once = editor.add_unique("", "Extracted from", "A.svg")
        assert editor.add_unique(once, "Extracted from", "A.svg") == once


# -------------------------------------------------------------------- #
# ensure_named
# -------------------------------------------------------------------- #


class TestEnsureNamedPosition:
    def test_adds_at_start_by_default(self, editor: TemplateEditor) -> None:
        assert editor.ensure_named("{{Svg lang|ar|de}}", "Svg lang", "dl", "en") == "{{Svg lang|dl=en|ar|de}}"

    def test_adds_at_start_explicitly(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|ar|de}}", "Svg lang", "dl", "en", position="start")
        assert result == "{{Svg lang|dl=en|ar|de}}"

    def test_adds_at_end(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|ar|de}}", "Svg lang", "dl", "en", position="end")
        assert result == "{{Svg lang|ar|de|dl=en}}"

    def test_start_puts_param_before_other_named_params(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|foo=bar|ar}}", "Svg lang", "dl", "en", position="start")
        assert result == "{{Svg lang|dl=en|ar|foo=bar}}"

    def test_end_puts_param_after_other_named_params(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|foo=bar|ar}}", "Svg lang", "dl", "en", position="end")
        assert result == "{{Svg lang|ar|foo=bar|dl=en}}"

    def test_existing_param_is_moved_to_start(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|ar|dl=en}}", "Svg lang", "dl", "en", position="start")
        assert result == "{{Svg lang|dl=en|ar}}"

    def test_existing_param_is_moved_to_end(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|dl=en|ar}}", "Svg lang", "dl", "en", position="end")
        assert result == "{{Svg lang|ar|dl=en}}"

    def test_template_without_params_gets_the_param(self, editor: TemplateEditor) -> None:
        assert editor.ensure_named("{{Svg lang}}", "Svg lang", "dl", "en") == "{{Svg lang|dl=en}}"

    def test_numbered_params_are_normalized(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|1=ar|2=de}}", "Svg lang", "dl", "en")
        assert result == "{{Svg lang|dl=en|ar|de}}"

    def test_empty_positional_slots_are_dropped(self, editor: TemplateEditor) -> None:
        assert editor.ensure_named("{{Svg lang||ar}}", "Svg lang", "dl", "en") == "{{Svg lang|dl=en|ar}}"


class TestEnsureNamedReplace:
    def test_keeps_existing_value_by_default(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|ar|dl=fr}}", "Svg lang", "dl", "en")
        assert result == "{{Svg lang|dl=fr|ar}}"

    def test_replace_overwrites_existing_value(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|ar|dl=fr}}", "Svg lang", "dl", "en", replace=True)
        assert result == "{{Svg lang|dl=en|ar}}"

    def test_empty_value_is_filled_with_default(self, editor: TemplateEditor) -> None:
        assert editor.ensure_named("{{Svg lang|dl=|ar}}", "Svg lang", "dl", "en") == "{{Svg lang|dl=en|ar}}"

    def test_whitespace_only_value_counts_as_empty(self, editor: TemplateEditor) -> None:
        assert editor.ensure_named("{{Svg lang|dl=  |ar}}", "Svg lang", "dl", "en") == "{{Svg lang|dl=en|ar}}"

    def test_value_equal_to_default_is_left_alone(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|dl=en|ar}}"
        assert editor.ensure_named(text, "Svg lang", "dl", "en") == text

    def test_replace_with_same_value_changes_nothing(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|dl=en|ar}}"
        assert editor.ensure_named(text, "Svg lang", "dl", "en", replace=True) == text


class TestEnsureNamedDedupe:
    def test_target_param_is_always_unique_last_non_empty_value_wins(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|dl=fr|ar|dl=de}}", "Svg lang", "dl", "en")
        assert result == "{{Svg lang|dl=de|ar}}"
        assert result.count("dl=") == 1

    def test_later_empty_duplicate_does_not_erase_value(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|dl=fr|ar|dl=}}", "Svg lang", "dl", "en")
        assert result == "{{Svg lang|dl=fr|ar}}"

    def test_replace_collapses_all_duplicates_into_default(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|dl=fr|ar|dl=de}}", "Svg lang", "dl", "en", replace=True)
        assert result == "{{Svg lang|dl=en|ar}}"

    def test_target_param_stays_unique_even_when_dedupe_is_off(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|dl=a|dl=b|ar}}", "Svg lang", "dl", "en", dedupe=False)
        assert result == "{{Svg lang|dl=b|ar}}"

    def test_other_named_duplicates_are_collapsed_last_wins(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|ar|foo=1|foo=2}}", "Svg lang", "dl", "en")
        assert result == "{{Svg lang|dl=en|ar|foo=2}}"

    def test_other_named_duplicates_are_kept_when_dedupe_is_off(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|ar|foo=1|foo=2}}", "Svg lang", "dl", "en", dedupe=False)
        assert result == "{{Svg lang|dl=en|ar|foo=1|foo=2}}"

    def test_later_empty_duplicate_of_other_param_keeps_earlier_value(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|foo=1|foo=}}", "Svg lang", "dl", "en")
        assert result == "{{Svg lang|dl=en|foo=1}}"

    def test_earlier_empty_duplicate_of_other_param_is_replaced(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|foo=|foo=2}}", "Svg lang", "dl", "en")
        assert result == "{{Svg lang|dl=en|foo=2}}"

    def test_dedupe_of_other_params_ignores_name_case(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|Foo=1|foo=2}}", "Svg lang", "dl", "en")
        assert result == "{{Svg lang|dl=en|foo=2}}"

    def test_distinct_other_params_keep_their_order(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|b=2|ar|a=1}}", "Svg lang", "dl", "en")
        assert result == "{{Svg lang|dl=en|ar|b=2|a=1}}"


class TestEnsureNamedMatching:
    def test_param_name_match_ignores_case(self, editor: TemplateEditor) -> None:
        # The caller's spelling of the parameter name is the one that is written.
        result = editor.ensure_named("{{Svg lang|DL=fr|ar}}", "Svg lang", "dl", "en")
        assert result == "{{Svg lang|dl=fr|ar}}"

    def test_param_name_match_treats_underscore_as_space(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{T|default_lang=fr|ar}}", "T", "default lang", "en")
        assert result == "{{T|default lang=fr|ar}}"

    def test_template_name_spelling_in_text_is_preserved(self, editor: TemplateEditor) -> None:
        assert editor.ensure_named("{{svg lang|ar}}", "Svg lang", "dl", "en") == "{{svg lang|dl=en|ar}}"

    def test_surrounding_text_is_preserved(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("x {{Svg lang|ar}} y", "Svg lang", "dl", "en")
        assert result == "x {{Svg lang|dl=en|ar}} y"

    def test_only_the_first_matching_template_is_changed(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar}}\n{{Svg lang|de}}"
        assert editor.ensure_named(text, "Svg lang", "dl", "en") == "{{Svg lang|dl=en|ar}}\n{{Svg lang|de}}"

    def test_other_templates_are_untouched(self, editor: TemplateEditor) -> None:
        text = "{{Extracted from|1=A.svg}}\n{{Svg lang|ar}}"
        assert editor.ensure_named(text, "Svg lang", "dl", "en") == "{{Extracted from|1=A.svg}}\n{{Svg lang|dl=en|ar}}"

    def test_missing_template_returns_text_unchanged(self, editor: TemplateEditor) -> None:
        text = "{{Other|ar}}"
        assert editor.ensure_named(text, "Svg lang", "dl", "en") == text

    def test_empty_text_returns_empty_text(self, editor: TemplateEditor) -> None:
        assert editor.ensure_named("", "Svg lang", "dl", "en") == ""

    def test_works_with_any_template_and_param(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Foo|x|y}}", "Foo", "lang", "ar", position="end")
        assert result == "{{Foo|x|y|lang=ar}}"

    def test_nested_template_in_a_named_value_is_preserved(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang|ar|note={{x|y}}}}", "Svg lang", "dl", "en")
        assert result == "{{Svg lang|dl=en|ar|note={{x|y}}}}"


class TestEnsureNamedFormatting:
    def test_multiline_template_is_rebuilt_on_one_line(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang\n|ar\n|de\n}}", "Svg lang", "dl", "en")
        assert result == "{{Svg lang|dl=en|ar|de}}"

    def test_values_are_stripped(self, editor: TemplateEditor) -> None:
        result = editor.ensure_named("{{Svg lang| ar | foo = bar }}", "Svg lang", "dl", "en")
        assert result == "{{Svg lang|dl=en|ar|foo=bar}}"

    @pytest.mark.parametrize("position", ["start", "end"])
    @pytest.mark.parametrize("replace", [False, True])
    @pytest.mark.parametrize("dedupe", [False, True])
    def test_is_idempotent(self, editor: TemplateEditor, position: str, replace: bool, dedupe: bool) -> None:
        text = "{{Svg lang|ar|foo=1|dl=fr|foo=2|de}}"
        once = editor.ensure_named(text, "Svg lang", "dl", "en", position=position, replace=replace, dedupe=dedupe)
        twice = editor.ensure_named(once, "Svg lang", "dl", "en", position=position, replace=replace, dedupe=dedupe)
        assert once == twice


# -------------------------------------------------------------------- #
# delete_values
# -------------------------------------------------------------------- #


class TestDeleteValues:
    def test_removes_matching_positional_value(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|dl=en|ar|de|fr}}", "Svg lang", ["de"])
        assert result == "{{Svg lang|dl=en|ar|fr}}"

    def test_removes_several_values(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|dl=en|ar|de|fr}}", "Svg lang", ["ar", "fr"])
        assert result == "{{Svg lang|dl=en|de}}"

    def test_matching_ignores_case_by_default(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("{{Svg lang|ar|de}}", "Svg lang", ["DE"])
        assert result == "{{Svg lang|ar}}"

    def test_strict_editor_is_case_sensitive(self, strict_editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar|de}}"
        assert strict_editor.delete_values(text, "Svg lang", ["DE"]) == text

    def test_removing_every_value_leaves_an_empty_template(self, editor: TemplateEditor) -> None:
        assert editor.delete_values("{{Svg lang|ar}}", "Svg lang", ["ar"]) == "{{Svg lang}}"

    def test_unknown_value_returns_text_unchanged(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar|de}}"
        assert editor.delete_values(text, "Svg lang", ["xx"]) == text

    @pytest.mark.parametrize("values", [[], [""], ["", ""]])
    def test_empty_values_return_text_unchanged(self, editor: TemplateEditor, values: list[str]) -> None:
        text = "{{Svg lang|ar|de}}"
        assert editor.delete_values(text, "Svg lang", values) == text

    def test_missing_template_returns_text_unchanged(self, editor: TemplateEditor) -> None:
        text = "{{Other|ar}}"
        assert editor.delete_values(text, "Svg lang", ["ar"]) == text

    def test_other_templates_are_untouched(self, editor: TemplateEditor) -> None:
        text = "{{Other|ar}}\n{{Svg lang|ar|de}}"
        assert editor.delete_values(text, "Svg lang", ["ar"]) == "{{Other|ar}}\n{{Svg lang|de}}"

    def test_named_param_values_are_matched_too(self, editor: TemplateEditor) -> None:
        # Deletion is by value, whatever the parameter name is.
        assert editor.delete_values("{{Svg lang|dl=en|ar}}", "Svg lang", ["en"]) == "{{Svg lang|ar}}"

    def test_surrounding_text_is_preserved(self, editor: TemplateEditor) -> None:
        result = editor.delete_values("x {{Svg lang|ar|de}} y", "Svg lang", ["ar"])
        assert result == "x {{Svg lang|de}} y"

    def test_is_idempotent(self, editor: TemplateEditor) -> None:
        once = editor.delete_values("{{Svg lang|ar|de}}", "Svg lang", ["ar"])
        assert editor.delete_values(once, "Svg lang", ["ar"]) == once


# -------------------------------------------------------------------- #
# remove_named
# -------------------------------------------------------------------- #


class TestRemoveNamed:
    def test_removes_the_named_param(self, editor: TemplateEditor) -> None:
        assert editor.remove_named("{{Svg lang|dl=en|ar}}", "Svg lang", "dl") == "{{Svg lang|ar}}"

    def test_removes_every_occurrence(self, editor: TemplateEditor) -> None:
        result = editor.remove_named("{{Svg lang|dl=a|ar|dl=b}}", "Svg lang", "dl")
        assert result == "{{Svg lang|ar}}"

    def test_param_name_match_ignores_case_and_underscore(self, editor: TemplateEditor) -> None:
        assert editor.remove_named("{{T|Default_Lang=en|ar}}", "T", "default lang") == "{{T|ar}}"

    def test_param_with_empty_value_is_removed(self, editor: TemplateEditor) -> None:
        assert editor.remove_named("{{Svg lang|dl=|ar}}", "Svg lang", "dl") == "{{Svg lang|ar}}"

    def test_positional_values_are_never_removed(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar|de}}"
        assert editor.remove_named(text, "Svg lang", "dl") == text

    def test_other_named_params_are_kept(self, editor: TemplateEditor) -> None:
        assert editor.remove_named("{{Svg lang|dl=en|foo=bar}}", "Svg lang", "dl") == "{{Svg lang|foo=bar}}"

    def test_missing_param_returns_text_unchanged(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|foo=bar|ar}}"
        assert editor.remove_named(text, "Svg lang", "dl") == text

    def test_missing_template_returns_text_unchanged(self, editor: TemplateEditor) -> None:
        text = "{{Other|dl=en}}"
        assert editor.remove_named(text, "Svg lang", "dl") == text

    def test_other_templates_are_untouched(self, editor: TemplateEditor) -> None:
        text = "{{Other|dl=en}}\n{{Svg lang|dl=en|ar}}"
        assert editor.remove_named(text, "Svg lang", "dl") == "{{Other|dl=en}}\n{{Svg lang|ar}}"

    def test_is_idempotent(self, editor: TemplateEditor) -> None:
        once = editor.remove_named("{{Svg lang|dl=en|ar}}", "Svg lang", "dl")
        assert editor.remove_named(once, "Svg lang", "dl") == once


# -------------------------------------------------------------------- #
# Combinations of operations
# -------------------------------------------------------------------- #


class TestCombinedOperations:
    def test_merge_then_ensure_builds_the_expected_template(self, editor: TemplateEditor) -> None:
        text = editor.merge_positional("", "Svg lang", ["ar", "de"])
        text = editor.ensure_named(text, "Svg lang", "dl", "en")
        assert text == "{{Svg lang|dl=en|ar|de}}"

    def test_ensure_after_merge_restores_the_requested_position(self, editor: TemplateEditor) -> None:
        # merge_positional writes named params last, ensure_named moves ``dl`` back to the front.
        text = editor.merge_positional("{{Svg lang|dl=en|ar}}", "Svg lang", ["de"])
        assert text == "{{Svg lang|ar|de|dl=en}}"
        assert editor.ensure_named(text, "Svg lang", "dl", "en") == "{{Svg lang|dl=en|ar|de}}"

    def test_delete_then_merge(self, editor: TemplateEditor) -> None:
        text = editor.delete_values("{{Svg lang|ar|de}}", "Svg lang", ["de"])
        assert editor.merge_positional(text, "Svg lang", ["fr"]) == "{{Svg lang|ar|fr}}"

    def test_remove_then_ensure_resets_the_param(self, editor: TemplateEditor) -> None:
        text = editor.remove_named("{{Svg lang|dl=fr|ar}}", "Svg lang", "dl")
        assert editor.ensure_named(text, "Svg lang", "dl", "en") == "{{Svg lang|dl=en|ar}}"

    def test_one_editor_works_with_several_templates_in_the_same_text(self, editor: TemplateEditor) -> None:
        text = "{{Svg lang|ar}}\n{{Other|x}}"
        text = editor.merge_positional(text, "Svg lang", ["de"])
        text = editor.merge_positional(text, "Other", ["y"])
        assert text == "{{Svg lang|ar|de}}\n{{Other|x|y}}"


class TestGetArgs:
    """Tests for the _get_argument function."""

    def test_basic(self) -> None:
        text_raw = """{{Information |description={{en|1=Daily per capita supply of all meat, World}} |author = Our World In Data |date= 2022 |Other_versions={{Extracted from|1=Daily meat consumption per person, World, 2022.svg}}}}"""
        template = wtp.Template(text_raw)
        args_in = TemplateEditor._get_argument(template, ["other versions", "other_versions"])
        assert args_in is not None
        assert args_in.value == "{{Extracted from|1=Daily meat consumption per person, World, 2022.svg}}"
        assert args_in.name == "Other_versions"

    def test_basic_args(self) -> None:
        text_raw = """{{Extracted from| 1 =  Daily meat consumption per person, World, 2022.svg}}"""
        template = wtp.Template(text_raw)
        args_in = TemplateEditor._get_argument(template, ["1"])
        assert args_in is not None
        assert args_in.value == "  Daily meat consumption per person, World, 2022.svg"
        assert args_in.name == " 1 "

    def test_basic_args_not_named(self) -> None:
        text_raw = """ hello? {{Extracted from | Daily meat consumption per person, World, 2022.svg}} zz"""
        template = wtp.WikiText(text_raw).templates[0]
        assert template.name.strip() == "Extracted from"
        args_in = TemplateEditor._get_argument(template, ["1"])
        assert args_in is not None
        assert args_in.value.strip() == "Daily meat consumption per person, World, 2022.svg"
        assert args_in.name == "1"
