"""Tests for ``OtherVersionsUpdater.delete_params``."""

from __future__ import annotations

import pytest
import wikitextparser as wtp

from src.main_app.utils.new_wikitext.other_versions import OtherVersionsUpdater


@pytest.fixture
def updater() -> OtherVersionsUpdater:
    return OtherVersionsUpdater()


def svg_lang_values(text: str) -> list[str]:
    """Return the positional values of the first {{Svg lang}} template."""
    for tpl in wtp.parse(text).templates:
        if tpl.name.replace("_", " ").strip().lower() == "svg lang":
            return [a.value.strip() for a in tpl.arguments]
    return []


# ---------------------------------------------------------------- #
# Nothing to do
# ---------------------------------------------------------------- #


def test_returns_text_unchanged_when_no_svg_lang_template(updater):
    text = "{{Information\n|other versions={{Extracted from|1=File.svg}}\n}}"
    assert updater.delete_params(text, ["ar"]) == text


def test_returns_text_unchanged_for_plain_text(updater):
    text = "just some text without templates"
    assert updater.delete_params(text, ["ar"]) == text


def test_returns_text_unchanged_for_empty_text(updater):
    assert updater.delete_params("", ["ar"]) == ""


def test_returns_text_unchanged_when_delete_values_is_empty(updater):
    text = "{{Svg lang|ar|de|fr}}"
    assert updater.delete_params(text, []) == text


def test_returns_text_unchanged_when_value_not_present(updater):
    text = "{{Svg lang|ar|de|fr}}"
    assert updater.delete_params(text, ["es"]) == text


# ---------------------------------------------------------------- #
# Deleting values
# ---------------------------------------------------------------- #


def test_deletes_single_value(updater):
    result = updater.delete_params("{{Svg lang|ar|de|fr}}", ["de"])
    assert svg_lang_values(result) == ["ar", "fr"]


def test_deletes_first_value(updater):
    result = updater.delete_params("{{Svg lang|ar|de|fr}}", ["ar"])
    assert svg_lang_values(result) == ["de", "fr"]


def test_deletes_last_value(updater):
    result = updater.delete_params("{{Svg lang|ar|de|fr}}", ["fr"])
    assert svg_lang_values(result) == ["ar", "de"]


def test_deletes_multiple_values(updater):
    result = updater.delete_params("{{Svg lang|ar|de|fr|es}}", ["de", "es"])
    assert svg_lang_values(result) == ["ar", "fr"]


def test_deletes_adjacent_values(updater):
    result = updater.delete_params("{{Svg lang|ar|de|fr|es}}", ["de", "fr"])
    assert svg_lang_values(result) == ["ar", "es"]


def test_deletes_all_values(updater):
    result = updater.delete_params("{{Svg lang|ar|de}}", ["ar", "de"])
    assert svg_lang_values(result) == []


def test_ignores_unknown_values_mixed_with_known_ones(updater):
    result = updater.delete_params("{{Svg lang|ar|de|fr}}", ["xx", "de"])
    assert svg_lang_values(result) == ["ar", "fr"]


# ---------------------------------------------------------------- #
# Matching rules
# ---------------------------------------------------------------- #


def test_match_is_case_insensitive_on_template_values(updater):
    # delete_values are expected to be lowercase (see add_svg_langs).
    result = updater.delete_params("{{Svg lang|AR|De|fr}}", ["ar", "de"])
    assert svg_lang_values(result) == ["fr"]


def test_match_ignores_whitespace_around_values(updater):
    result = updater.delete_params("{{Svg lang| ar | de |fr}}", ["ar", "de"])
    assert svg_lang_values(result) == ["fr"]


@pytest.mark.parametrize(
    "template_name",
    ["Svg lang", "svg lang", "Svg_lang", "Svg Lang", " Svg lang "],
)
def test_template_name_matching_is_normalized(updater, template_name):
    text = "{{" + template_name + "|ar|de}}"
    result = updater.delete_params(text, ["ar"])
    assert svg_lang_values(result) == ["de"]


def test_does_not_delete_partial_matches(updater):
    result = updater.delete_params("{{Svg lang|ar|ara|de}}", ["ar"])
    assert svg_lang_values(result) == ["ara", "de"]


# ---------------------------------------------------------------- #
# Surrounding content
# ---------------------------------------------------------------- #


def test_other_templates_are_untouched(updater):
    text = "{{Extracted from|1=File.svg}}\n{{Svg lang|ar|de}}"
    result = updater.delete_params(text, ["ar"])
    assert "{{Extracted from|1=File.svg}}" in result
    assert svg_lang_values(result) == ["de"]


def test_other_templates_with_same_values_are_untouched(updater):
    text = "{{Other|ar|de}}\n{{Svg lang|ar|de}}"
    result = updater.delete_params(text, ["ar"])
    assert "{{Other|ar|de}}" in result
    assert svg_lang_values(result) == ["de"]


def test_text_outside_template_is_preserved(updater):
    text = "before {{Svg lang|ar|de}} after"
    result = updater.delete_params(text, ["ar"])
    assert result.startswith("before ")
    assert result.endswith(" after")


def test_deletes_inside_information_other_versions(updater):
    text = (
        "== {{int:filedesc}} ==\n"
        "{{Information\n"
        "|description=Test\n"
        "|other versions={{Svg lang|ar|de|fr}}\n"
        "|source=Own work\n"
        "}}"
    )
    result = updater.delete_params(text, ["de"])
    assert svg_lang_values(result) == ["ar", "fr"]
    assert "|description=Test" in result
    assert "|source=Own work" in result


def test_result_is_still_valid_template(updater):
    result = updater.delete_params("{{Svg lang|ar|de|fr}}", ["de"])

    has = OtherVersionsUpdater()._find_template(wtp.parse(result), "svg lang")
    assert has is not None

    assert result.startswith("{{") and result.endswith("}}")


# ---------------------------------------------------------------- #
# Idempotency
# ---------------------------------------------------------------- #


def test_is_idempotent(updater):
    once = updater.delete_params("{{Svg lang|ar|de|fr}}", ["de"])
    twice = updater.delete_params(once, ["de"])
    assert once == twice
