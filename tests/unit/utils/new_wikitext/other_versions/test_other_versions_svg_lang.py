"""Tests for adding ``{{Svg lang|xx}}`` to ``|other versions =`` via OtherVersionsUpdater."""

from __future__ import annotations

import pytest
from src.main_app.utils.new_wikitext.other_versions import (
    OtherVersionsUpdater,
    add_svg_langs_to_other_versions,
)


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


class TestFunctionalWrapper:
    def test_wrapper_adds_languages(self):
        result = add_svg_langs_to_other_versions(text=make_info("{{Svg lang|dl=en|ar}}"), langs=["de"])
        assert "{{Svg lang|dl=en|ar|de}}" in result

    def test_wrapper_without_main_template(self):
        assert add_svg_langs_to_other_versions(text="plain", langs=["ar"]) == "plain"


class TestDefaultLanguage:
    """The English default language is always explicit and comes first."""

    def test_adds_dl_en_before_language_codes(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), ["ar", "de", "fr"])
        assert "{{Svg lang|dl=en|ar|de|fr}}" in result

    def test_moves_existing_dl_to_first_position(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar|dl=fr|de}}")
        result = updater.add_svg_langs(text, ["fr"])
        assert "{{Svg lang|dl=fr|ar|de|fr}}" in result

    def test_replace_dl(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar|dl=fr|de}}")
        result = updater.add_svg_langs(text, ["fr"], replace_dl=True)
        assert "{{Svg lang|dl=en|ar|de|fr}}" in result

    def test_does_not_duplicate_dl_parameter(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=fr|ar|dl=de}}")
        result = updater.add_svg_langs(text, ["fr"], replace_dl=True)
        assert result.count("dl=") == 1
        assert "{{Svg lang|dl=en|ar|fr}}" in result

    def test_dl_at_end(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_svg_langs(make_info(), ["ar", "de"], dl_position="end")
        assert "{{Svg lang|ar|de|dl=en}}" in result

    def test_dedupe_other_named(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar|foo=1|foo=2}}")
        result = updater.add_svg_langs(text, ["de"])
        assert "{{Svg lang|dl=en|ar|de|foo=2}}" in result

    def test_adds_dl_en_when_no_new_languages_are_needed(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar|de}}")
        result = updater.add_svg_langs(text, ["ar", "de"])
        assert "{{Svg lang|dl=en|ar|de}}" in result
