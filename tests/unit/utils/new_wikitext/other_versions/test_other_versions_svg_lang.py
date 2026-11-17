"""Tests for adding ``{{Svg lang|xx}}`` to ``|other versions =`` via OtherVersionsUpdater."""

from __future__ import annotations

import pytest
from src.main_app.utils.new_wikitext.other_versions import OtherVersionsUpdater


@pytest.fixture
def updater() -> OtherVersionsUpdater:
    return OtherVersionsUpdater()


def make_info(other_versions: str | None = None) -> str:
    """Build a minimal {{Information}} template, optionally with other versions."""
    lines = [
        "{{Information",
        "|description={{en|1=Daily and total confirmed COVID-19 deaths, Africa}}",
        "|author = Our World In Data",
    ]
    if other_versions is not None:
        lines.append(f"|other versions = {other_versions}")
    lines.append("}}")
    return "\n".join(lines)


class TestCreateParameter:
    """The ``other versions`` parameter / template does not exist yet."""

    def test_creates_param_and_template(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Information\n|description=x\n}}"
        result = updater.add_svg_langs(text, ["ar", "de"])
        assert result == "{{Information\n|description=x\n|other versions={{Svg lang|dl=en|ar|de}}}}"

    def test_fills_empty_param(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Information\n|description=x\n|other versions=\n}}"
        result = updater.add_svg_langs(text, ["ar"])
        assert "{{Svg lang|dl=en|ar}}" in result
        assert result.count("other versions") == 1

    def test_adds_svg_lang_after_other_template(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Extracted from|1=A.svg}}")
        result = updater.add_svg_langs(text, ["ar"])
        assert "{{Extracted from|1=A.svg}}\n{{Svg lang|dl=en|ar}}" in result

    def test_single_language(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), ["fr"])
        assert "{{Svg lang|dl=en|fr}}" in result

    def test_other_versions_with_underscore_name_is_reused(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Information\n|other_versions = {{Svg lang|dl=en|ar}}\n}}"
        result = updater.add_svg_langs(text, ["de"])
        assert "{{Svg lang|dl=en|ar|de}}" in result
        assert "other versions" not in result


class TestMergeIntoExisting:
    """``{{Svg lang}}`` already exists and new languages are merged into it."""

    def test_appends_new_languages_in_order(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar|de|fr|fa}}")
        result = updater.add_svg_langs(text, ["es", "it"])
        assert "{{Svg lang|dl=en|ar|de|fr|fa|es|it}}" in result

    def test_does_not_create_second_template(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar}}")
        result = updater.add_svg_langs(text, ["de"])
        assert result.count("{{Svg lang") == 1

    def test_only_new_languages_are_added(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar|de}}")
        result = updater.add_svg_langs(text, ["de", "es"])
        assert "{{Svg lang|dl=en|ar|de|es}}" in result

    def test_preserves_other_text_in_the_page(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar}}")
        result = updater.add_svg_langs(text, ["de"])
        assert "|description={{en|1=Daily and total confirmed COVID-19 deaths, Africa}}" in result
        assert "|author = Our World In Data" in result

    def test_explicit_numbered_params_are_normalized(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|1=ar|2=de}}")
        result = updater.add_svg_langs(text, ["fr"])
        assert "{{Svg lang|dl=en|ar|de|fr}}" in result

    def test_named_params_are_preserved(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar|foo=bar}}")
        result = updater.add_svg_langs(text, ["de"])
        assert "{{Svg lang|dl=en|ar|de|foo=bar}}" in result

    def test_template_name_case_is_respected_when_matching(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{svg lang|ar}}")
        result = updater.add_svg_langs(text, ["de"])
        assert result.lower().count("{{svg lang") == 1
        assert "|ar|de}}" in result

    def test_keeps_other_templates_in_param(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Extracted from|1=A.svg}}\n{{Svg lang|dl=en|ar}}")
        result = updater.add_svg_langs(text, ["de"])
        assert "{{Extracted from|1=A.svg}}" in result
        assert "{{Svg lang|dl=en|ar|de}}" in result

    def test_template_before_other_templates_keeps_its_position(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar}}\n{{Extracted from|1=A.svg}}")
        result = updater.add_svg_langs(text, ["de"])
        assert "{{Svg lang|dl=en|ar|de}}\n{{Extracted from|1=A.svg}}" in result


class TestDuplicates:
    """No duplicates and no change when nothing new is added."""

    def test_existing_language_keeps_normalized_text_unchanged(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar|de|fr|fa}}")
        assert updater.add_svg_langs(text, ["de"]) == text

    def test_all_languages_existing_keeps_normalized_text_unchanged(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar|de}}")
        assert updater.add_svg_langs(text, ["ar", "de"]) == text

    def test_case_insensitive_duplicates(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar|de}}")
        assert updater.add_svg_langs(text, ["AR", "De"]) == text

    def test_duplicates_inside_input_are_collapsed(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), ["ar", "ar", "AR"])
        assert "{{Svg lang|dl=en|ar}}" in result

    def test_is_idempotent(self, updater: OtherVersionsUpdater) -> None:
        once = updater.add_svg_langs(make_info(), ["ar", "de"])
        twice = updater.add_svg_langs(once, ["ar", "de"])
        assert once == twice


class TestInputNormalization:
    """Language codes are cleaned before use."""

    def test_codes_are_lowercased(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), ["AR", "De"])
        assert "{{Svg lang|dl=en|ar|de}}" in result

    def test_blank_and_whitespace_items_are_ignored(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), ["", "  ", "ar"])
        assert "{{Svg lang|dl=en|ar}}" in result

    @pytest.mark.parametrize("langs", [[], [""], ["  "]])
    def test_no_valid_languages_returns_text_unchanged(self, updater, langs):
        text = make_info("{{Svg lang|dl=en|ar}}")
        assert updater.add_svg_langs(text, langs) == text

    def test_accepts_any_iterable(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), (lang for lang in ["ar", "de"]))
        assert "{{Svg lang|dl=en|ar|de}}" in result

    def test_tuple_input_is_accepted(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), ("ar", "de"))
        assert "{{Svg lang|dl=en|ar|de}}" in result

    def test_none_items_are_ignored(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), [None, "ar"])
        assert "{{Svg lang|dl=en|ar}}" in result


class TestSorting:
    def test_sort_false_keeps_insertion_order(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), ["fr", "ar", "de"])
        assert "{{Svg lang|dl=en|fr|ar|de}}" in result

    def test_sort_true_orders_alphabetically(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), ["fr", "ar", "de"], sort=True)
        assert "{{Svg lang|dl=en|ar|de|fr}}" in result

    def test_sort_true_applies_to_merged_list(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|fr|ar}}")
        result = updater.add_svg_langs(text, ["de"], sort=True)
        assert "{{Svg lang|dl=en|ar|de|fr}}" in result

    def test_sort_does_not_move_dl(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), ["fr", "ar"], sort=True)
        assert "{{Svg lang|dl=en|ar|fr}}" in result


class TestMainTemplateLookup:
    def test_no_main_template_returns_text_unchanged(self, updater: OtherVersionsUpdater) -> None:
        text = "Just some text without templates"
        assert updater.add_svg_langs(text, ["ar"]) == text

    def test_other_main_template_is_ignored(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Other|description=x}}"
        assert updater.add_svg_langs(text, ["ar"]) == text

    def test_main_template_name_is_case_insensitive(self, updater: OtherVersionsUpdater) -> None:
        text = "{{information\n|description=x\n}}"
        result = updater.add_svg_langs(text, ["ar"])
        assert "{{Svg lang|dl=en|ar}}" in result

    def test_custom_main_template_name(self):
        custom = OtherVersionsUpdater(main_template_name="Artwork")
        text = "{{Artwork\n|description=x\n}}"
        assert "{{Svg lang|dl=en|ar}}" in custom.add_svg_langs(text, ["ar"])
        info = "{{Information\n|description=x\n}}"
        assert custom.add_svg_langs(info, ["ar"]) == info

    def test_custom_param_name_is_used_when_created(self):
        custom = OtherVersionsUpdater(param_names=["versions"])
        result = custom.add_svg_langs("{{Information\n|description=x\n}}", ["ar"])
        assert "|versions={{Svg lang|dl=en|ar}}" in result

    def test_template_embedded_in_larger_page(self, updater: OtherVersionsUpdater) -> None:
        page = "== {{int:filedesc}} ==\n" + make_info("{{Svg lang|dl=en|ar}}") + "\n\n== License ==\n{{cc-by-4.0}}"
        result = updater.add_svg_langs(page, ["de"])
        assert "{{Svg lang|dl=en|ar|de}}" in result
        assert result.startswith("== {{int:filedesc}} ==")
        assert result.endswith("{{cc-by-4.0}}")

    def test_svg_lang_outside_the_main_template_is_not_touched(self, updater: OtherVersionsUpdater) -> None:
        page = make_info("{{Svg lang|dl=en|ar}}") + "\n{{Svg lang|fa}}"
        result = updater.add_svg_langs(page, ["de"])
        assert "{{Svg lang|dl=en|ar|de}}" in result
        assert result.endswith("{{Svg lang|fa}}")


class TestDefaultLanguage:
    """The English default language is always explicit and comes first."""

    def test_adds_dl_en_before_language_codes(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), ["ar", "de", "fr"])
        assert "{{Svg lang|dl=en|ar|de|fr}}" in result

    def test_keeps_existing_dl_value_and_moves_it_to_first_position(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar|dl=fr|de}}")
        result = updater.add_svg_langs(text, ["fr"])
        assert "{{Svg lang|dl=fr|ar|de|fr}}" in result

    def test_replace_dl_overwrites_existing_value(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar|dl=fr|de}}")
        result = updater.add_svg_langs(text, ["fr"], replace_dl=True)
        assert "{{Svg lang|dl=en|ar|de|fr}}" in result

    def test_does_not_duplicate_dl_parameter(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=fr|ar|dl=de}}")
        result = updater.add_svg_langs(text, ["fr"], replace_dl=True)
        assert result.count("dl=") == 1
        assert "{{Svg lang|dl=en|ar|fr}}" in result

    def test_duplicate_dl_without_replace_keeps_last_non_empty_value(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=fr|ar|dl=de}}")
        result = updater.add_svg_langs(text, ["fr"])
        assert result.count("dl=") == 1
        assert "{{Svg lang|dl=de|ar|fr}}" in result

    def test_empty_dl_is_filled_with_en(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=|ar}}")
        result = updater.add_svg_langs(text, ["de"])
        assert "{{Svg lang|dl=en|ar|de}}" in result

    def test_adds_dl_en_when_no_new_languages_are_needed(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar|de}}")
        result = updater.add_svg_langs(text, ["ar", "de"])
        assert "{{Svg lang|dl=en|ar|de}}" in result

    def test_adds_dl_en_when_language_list_is_empty(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar|de}}")
        result = updater.add_svg_langs(text, [])
        assert "{{Svg lang|dl=en|ar|de}}" in result

    def test_does_not_create_svg_lang_when_there_is_nothing_to_add(self, updater: OtherVersionsUpdater) -> None:
        text = make_info()
        assert updater.add_svg_langs(text, []) == text

    def test_does_not_create_svg_lang_when_other_versions_has_only_other_templates(
        self, updater: OtherVersionsUpdater
    ) -> None:
        text = make_info("{{Extracted from|1=A.svg}}")
        assert updater.add_svg_langs(text, []) == text


class TestDlPosition:
    def test_dl_at_start_is_the_default(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), ["ar", "de"], dl_position="start")
        assert "{{Svg lang|dl=en|ar|de}}" in result

    def test_dl_at_end_on_new_template(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), ["ar", "de"], dl_position="end")
        assert "{{Svg lang|ar|de|dl=en}}" in result

    def test_dl_at_end_on_existing_template(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar}}")
        result = updater.add_svg_langs(text, ["de"], dl_position="end")
        assert "{{Svg lang|ar|de|dl=en}}" in result

    def test_dl_at_end_keeps_other_named_params_before_it(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar|foo=bar}}")
        result = updater.add_svg_langs(text, ["de"], dl_position="end")
        assert "{{Svg lang|ar|de|foo=bar|dl=en}}" in result

    def test_dl_at_end_when_nothing_new_is_added(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar}}")
        result = updater.add_svg_langs(text, ["ar"], dl_position="end")
        assert "{{Svg lang|ar|dl=en}}" in result

    def test_dl_at_end_is_idempotent(self, updater: OtherVersionsUpdater) -> None:
        once = updater.add_svg_langs(make_info(), ["ar", "de"], dl_position="end")
        assert updater.add_svg_langs(once, ["ar", "de"], dl_position="end") == once

    def test_dl_at_end_with_replace(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=fr|ar}}")
        result = updater.add_svg_langs(text, ["de"], dl_position="end", replace_dl=True)
        assert "{{Svg lang|ar|de|dl=en}}" in result


class TestReplaceDl:
    def test_default_keeps_existing_value(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=fr|ar}}")
        assert updater.add_svg_langs(text, ["ar"]) == text

    def test_replace_overwrites_value_even_without_new_languages(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=fr|ar}}")
        result = updater.add_svg_langs(text, ["ar"], replace_dl=True)
        assert "{{Svg lang|dl=en|ar}}" in result

    def test_replace_has_no_effect_when_value_is_already_en(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar}}")
        assert updater.add_svg_langs(text, ["ar"], replace_dl=True) == text

    def test_replace_is_idempotent(self, updater: OtherVersionsUpdater) -> None:
        once = updater.add_svg_langs(make_info("{{Svg lang|dl=fr|ar}}"), ["de"], replace_dl=True)
        assert updater.add_svg_langs(once, ["de"], replace_dl=True) == once


class TestDedupeNamed:
    def test_other_named_duplicates_are_collapsed_by_default(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar|foo=1|foo=2}}")
        result = updater.add_svg_langs(text, ["de"])
        assert "{{Svg lang|dl=en|ar|de|foo=2}}" in result

    def test_other_named_duplicates_are_kept_when_disabled(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar|foo=1|foo=2}}")
        result = updater.add_svg_langs(text, ["de"], dedupe_named=False)
        assert "{{Svg lang|dl=en|ar|de|foo=1|foo=2}}" in result

    def test_dl_is_unique_even_when_dedupe_is_disabled(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=fr|ar|dl=de}}")
        result = updater.add_svg_langs(text, ["fr"], dedupe_named=False, replace_dl=True)
        assert result.count("dl=") == 1
        assert "{{Svg lang|dl=en|ar|fr}}" in result


class TestDeleteValues:
    def test_removes_given_language_codes(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar|de|fr}}")
        result = updater.add_svg_langs(text, [], values_to_delete=["de"])
        assert "{{Svg lang|dl=en|ar|fr}}" in result

    def test_removes_several_codes(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar|de|fr}}")
        result = updater.add_svg_langs(text, [], values_to_delete=["ar", "fr"])
        assert "{{Svg lang|dl=en|de}}" in result

    def test_deletion_is_case_insensitive(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar|de}}")
        result = updater.add_svg_langs(text, [], values_to_delete=["DE"])
        assert "{{Svg lang|dl=en|ar}}" in result

    def test_removed_codes_are_not_added_back(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar|fr}}")
        result = updater.add_svg_langs(text, ["es", "de"], values_to_delete=["de"])
        assert "{{Svg lang|dl=en|ar|fr|es}}" in result

    def test_deleting_and_adding_the_same_code_removes_it(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar|de}}")
        result = updater.add_svg_langs(text, ["ar"], values_to_delete=["ar"])
        assert "{{Svg lang|dl=en|de}}" in result

    def test_deleting_every_code_keeps_the_template_with_dl(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar}}")
        result = updater.add_svg_langs(text, [], values_to_delete=["ar"])
        assert "{{Svg lang|dl=en}}" in result

    def test_unknown_code_changes_nothing(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar}}")
        assert updater.add_svg_langs(text, [], values_to_delete=["xx"]) == text

    @pytest.mark.parametrize("values_to_delete", [[], [""], None])
    def test_blank_values_to_delete_change_nothing(self, updater: OtherVersionsUpdater, values_to_delete) -> None:
        text = make_info("{{Svg lang|dl=en|ar}}")
        assert updater.add_svg_langs(text, [], values_to_delete=values_to_delete) == text

    def test_deleting_en_does_not_lose_the_default_language(self, updater: OtherVersionsUpdater) -> None:
        # ``dl=en`` has the value "en", so it matches the deletion, but it is put back afterwards.
        text = make_info("{{Svg lang|dl=en|ar}}")
        assert updater.add_svg_langs(text, [], values_to_delete=["en"]) == text

    def test_deletion_works_without_main_template_but_nothing_is_added(self, updater: OtherVersionsUpdater) -> None:
        # editor.delete_values works on the whole text; adding/ensuring still needs the main template.
        text = "{{Svg lang|dl=en|ar}}"
        assert updater.add_svg_langs(text, ["de"], values_to_delete=["ar"]) == "{{Svg lang|dl=en}}"


class TestCombinedOptions:
    def test_all_options_together(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=fr|ar|de|foo=1|foo=2}}")
        result = updater.add_svg_langs(
            text,
            ["es", "AR", "it"],
            sort=True,
            values_to_delete=["de"],
            dl_position="end",
            replace_dl=True,
            dedupe_named=True,
        )
        assert "{{Svg lang|ar|es|it|foo=2|dl=en}}" in result

    @pytest.mark.parametrize("position", ["start", "end"])
    @pytest.mark.parametrize("replace_dl", [False, True])
    @pytest.mark.parametrize("dedupe_named", [False, True])
    @pytest.mark.parametrize("sort", [False, True])
    def test_every_option_combination_is_idempotent(
        self,
        updater: OtherVersionsUpdater,
        position: str,
        replace_dl: bool,
        dedupe_named: bool,
        sort: bool,
    ) -> None:
        text = make_info("{{Svg lang|fr|dl=fa|ar|foo=1|foo=2}}")
        kwargs = {
            "sort": sort,
            "dl_position": position,
            "replace_dl": replace_dl,
            "dedupe_named": dedupe_named,
        }
        once = updater.add_svg_langs(text, ["de", "es"], **kwargs)
        twice = updater.add_svg_langs(once, ["de", "es"], **kwargs)
        assert once == twice

    @pytest.mark.parametrize("position", ["start", "end"])
    def test_dl_has_exactly_one_value_in_every_mode(self, updater: OtherVersionsUpdater, position: str) -> None:
        text = make_info("{{Svg lang|dl=a|ar|dl=b|dl=}}")
        result = updater.add_svg_langs(text, ["de"], dl_position=position)
        assert result.count("dl=") == 1
