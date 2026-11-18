"""Tests for the generic operations of OtherVersionsUpdater.

The updater only decides *where* to work (the ``other versions`` parameter of the
main template) and delegates the template logic to :class:`TemplateEditor`.
"""

from __future__ import annotations

import pytest
from src.main_app.parsers.template_editor import TemplateEditor
from src.main_app.utils.new_wikitext.other_versions import OtherVersionsUpdater


@pytest.fixture
def updater() -> OtherVersionsUpdater:
    return OtherVersionsUpdater()


def make_info(other_versions: str | None = None) -> str:
    """Build a minimal {{Information}} template, optionally with other versions."""
    lines = [
        "{{Information",
        "|description=x",
        "|author = Someone",
    ]
    if other_versions is not None:
        lines.append(f"|other versions = {other_versions}")
    lines.append("}}")
    return "\n".join(lines)


# -------------------------------------------------------------------- #
# Construction and editor injection
# -------------------------------------------------------------------- #


class TestConstruction:
    def test_defaults(self, updater: OtherVersionsUpdater) -> None:
        assert updater.main_template_name == "Information"
        assert updater.param_names == ["other versions", "other_versions"]
        assert updater.case_insensitive is True
        assert isinstance(updater.editor, TemplateEditor)

    def test_default_editor_follows_case_insensitive_flag(self) -> None:
        assert OtherVersionsUpdater(case_insensitive=False).editor.case_insensitive is False
        assert OtherVersionsUpdater(case_insensitive=True).editor.case_insensitive is True

    def test_custom_editor_is_used_as_is(self) -> None:
        editor = TemplateEditor(case_insensitive=False)
        assert OtherVersionsUpdater(editor=editor).editor is editor

    def test_param_names_list_is_copied(self) -> None:
        names = ["versions"]
        custom = OtherVersionsUpdater(param_names=names)
        names.append("other")
        assert custom.param_names == ["versions"]

    def test_empty_param_names_fall_back_to_defaults(self) -> None:
        assert OtherVersionsUpdater(param_names=[]).param_names == ["other versions", "other_versions"]

    def test_operations_are_delegated_to_the_injected_editor(self) -> None:
        calls: list[str] = []

        class RecordingEditor(TemplateEditor):
            def merge_positional(self, text, template_name, values, *, sort=False):
                calls.append("merge_positional")
                return super().merge_positional(text, template_name, values, sort=sort)

            def add_unique(self, text, template_name, first_param_value):
                calls.append("add_unique")
                return super().add_unique(text, template_name, first_param_value)

            def ensure_named(self, text, template_name, param_name, default_value, **kwargs):
                calls.append("ensure_named")
                return super().ensure_named(text, template_name, param_name, default_value, **kwargs)

            def delete_values(self, text, template_name, values):
                calls.append("delete_values")
                return super().delete_values(text, template_name, values)

            def remove_named(self, text, template_name, param_name):
                calls.append("remove_named")
                return super().remove_named(text, template_name, param_name)

        custom = OtherVersionsUpdater(editor=RecordingEditor())
        text = make_info("{{Svg lang|ar}}")
        custom.merge_values(text, "Svg lang", ["de"])
        custom.add_template(text, "Extracted from", "A.svg")
        custom.ensure_named_param(text, "Svg lang", "dl", "en")
        # custom.delete_values(text, "Svg lang", ["ar"])
        custom.remove_named_param(text, "Svg lang", "dl")

        assert calls == ["merge_positional", "add_unique", "ensure_named", "remove_named"]

    def test_editor_is_not_called_when_main_template_is_missing(self) -> None:
        calls: list[str] = []

        class RecordingEditor(TemplateEditor):
            def merge_positional(self, text, template_name, values, *, sort=False):
                calls.append("merge_positional")
                return super().merge_positional(text, template_name, values, sort=sort)

        custom = OtherVersionsUpdater(editor=RecordingEditor())
        assert custom.merge_values("{{Other|x=1}}", "Svg lang", ["ar"]) == "{{Other|x=1}}"
        assert calls == []


# -------------------------------------------------------------------- #
# merge_values
# -------------------------------------------------------------------- #


class TestMergeValues:
    def test_creates_param_and_template(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Information\n|description=x\n}}"
        result = updater.merge_values(text, "Svg lang", ["ar", "de"])
        assert result == "{{Information\n|description=x\n|other versions={{Svg lang|ar|de}}}}"

    def test_creates_template_inside_existing_param(self, updater: OtherVersionsUpdater) -> None:
        result = updater.merge_values(make_info("{{Extracted from|1=A.svg}}"), "Svg lang", ["ar"])
        assert "{{Extracted from|1=A.svg}}\n{{Svg lang|ar}}" in result

    def test_merges_into_existing_template(self, updater: OtherVersionsUpdater) -> None:
        result = updater.merge_values(make_info("{{Svg lang|ar}}"), "Svg lang", ["de"])
        assert "{{Svg lang|ar|de}}" in result

    def test_sort(self, updater: OtherVersionsUpdater) -> None:
        result = updater.merge_values(make_info(), "Svg lang", ["fr", "ar"], sort=True)
        assert "{{Svg lang|ar|fr}}" in result

    def test_works_with_any_template(self, updater: OtherVersionsUpdater) -> None:
        result = updater.merge_values(make_info("{{Other versions|a}}"), "Other versions", ["b"])
        assert "{{Other versions|a|b}}" in result

    def test_no_new_values_returns_text_unchanged(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar|de}}")
        assert updater.merge_values(text, "Svg lang", ["de"]) == text

    @pytest.mark.parametrize("values", [[], [""], ["  "]])
    def test_blank_values_return_text_unchanged(self, updater: OtherVersionsUpdater, values: list[str]) -> None:
        text = make_info()
        assert updater.merge_values(text, "Svg lang", values) == text

    def test_missing_main_template_returns_text_unchanged(self, updater: OtherVersionsUpdater) -> None:
        assert updater.merge_values("plain text", "Svg lang", ["ar"]) == "plain text"

    def test_case_sensitive_updater_keeps_different_case_values(self) -> None:
        strict = OtherVersionsUpdater(case_insensitive=False)
        result = strict.merge_values(make_info("{{Svg lang|ar}}"), "Svg lang", ["AR"])
        assert "{{Svg lang|ar|AR}}" in result

    def test_is_idempotent(self, updater: OtherVersionsUpdater) -> None:
        once = updater.merge_values(make_info(), "Svg lang", ["ar", "de"])
        assert updater.merge_values(once, "Svg lang", ["ar", "de"]) == once


# -------------------------------------------------------------------- #
# add_template
# -------------------------------------------------------------------- #


class TestAddTemplate:
    def test_creates_param_and_template(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Information\n|description=x\n}}"
        result = updater.add_template(text, "Extracted from", "A.svg")
        assert result == "{{Information\n|description=x\n|other versions={{Extracted from|1=A.svg}}}}"

    def test_appends_after_existing_template(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_template(make_info("{{Svg lang|ar}}"), "Extracted from", "A.svg")
        assert "{{Svg lang|ar}}\n{{Extracted from|1=A.svg}}" in result

    def test_skips_duplicate(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Extracted from|1=A.svg}}")
        assert updater.add_template(text, "Extracted from", "A.svg") == text

    def test_duplicate_check_ignores_case_and_underscores(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Extracted from|1=My_File.svg}}")
        assert updater.add_template(text, "Extracted from", "my file.SVG") == text

    def test_different_value_is_added(self, updater: OtherVersionsUpdater) -> None:
        result = updater.add_template(make_info("{{Extracted from|1=A.svg}}"), "Extracted from", "B.svg")
        assert "{{Extracted from|1=A.svg}}\n{{Extracted from|1=B.svg}}" in result

    def test_missing_main_template_returns_text_unchanged(self, updater: OtherVersionsUpdater) -> None:
        assert updater.add_template("plain", "Extracted from", "A.svg") == "plain"

    def test_is_idempotent(self, updater: OtherVersionsUpdater) -> None:
        once = updater.add_template(make_info(), "Extracted from", "A.svg")
        assert updater.add_template(once, "Extracted from", "A.svg") == once

    def test_can_be_combined_with_svg_langs(self, updater: OtherVersionsUpdater) -> None:
        text = updater.add_template(make_info(), "Extracted from", "A.svg")
        text = updater.add_svg_langs(text, ["ar"])
        assert "{{Extracted from|1=A.svg}}\n{{Svg lang|dl=en|ar}}" in text


# -------------------------------------------------------------------- #
# ensure_named_param
# -------------------------------------------------------------------- #


class TestEnsureNamedParam:
    def test_adds_param_at_start_by_default(self, updater: OtherVersionsUpdater) -> None:
        result = updater.ensure_named_param(make_info("{{Svg lang|ar|de}}"), "Svg lang", "dl", "en")
        assert "{{Svg lang|dl=en|ar|de}}" in result

    def test_adds_param_at_end(self, updater: OtherVersionsUpdater) -> None:
        result = updater.ensure_named_param(make_info("{{Svg lang|ar|de}}"), "Svg lang", "dl", "en", position="end")
        assert "{{Svg lang|ar|de|dl=en}}" in result

    def test_keeps_existing_value_by_default(self, updater: OtherVersionsUpdater) -> None:
        result = updater.ensure_named_param(make_info("{{Svg lang|ar|dl=fr}}"), "Svg lang", "dl", "en")
        assert "{{Svg lang|dl=fr|ar}}" in result

    def test_replace(self, updater: OtherVersionsUpdater) -> None:
        result = updater.ensure_named_param(make_info("{{Svg lang|ar|dl=fr}}"), "Svg lang", "dl", "en", replace=True)
        assert "{{Svg lang|dl=en|ar}}" in result

    def test_dedupe_can_be_disabled(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar|foo=1|foo=2}}")
        kept = updater.ensure_named_param(text, "Svg lang", "dl", "en", dedupe=False)
        collapsed = updater.ensure_named_param(text, "Svg lang", "dl", "en", dedupe=True)
        assert "{{Svg lang|dl=en|ar|foo=1|foo=2}}" in kept
        assert "{{Svg lang|dl=en|ar|foo=2}}" in collapsed

    def test_only_the_named_template_is_changed(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Extracted from|1=A.svg}}\n{{Svg lang|ar}}")
        result = updater.ensure_named_param(text, "Svg lang", "dl", "en")
        assert "{{Extracted from|1=A.svg}}\n{{Svg lang|dl=en|ar}}" in result

    def test_template_not_in_param_returns_text_unchanged(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Extracted from|1=A.svg}}")
        assert updater.ensure_named_param(text, "Svg lang", "dl", "en") == text

    def test_missing_param_returns_text_unchanged(self, updater: OtherVersionsUpdater) -> None:
        text = make_info()
        assert updater.ensure_named_param(text, "Svg lang", "dl", "en") == text

    def test_missing_main_template_returns_text_unchanged(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Svg lang|ar}}"
        assert updater.ensure_named_param(text, "Svg lang", "dl", "en") == text

    def test_does_not_touch_templates_outside_the_param(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar}}") + "\n{{Svg lang|fa}}"
        result = updater.ensure_named_param(text, "Svg lang", "dl", "en")
        assert result.endswith("{{Svg lang|fa}}")

    def test_works_with_any_template(self, updater: OtherVersionsUpdater) -> None:
        result = updater.ensure_named_param(make_info("{{Foo|x}}"), "Foo", "lang", "ar")
        assert "{{Foo|lang=ar|x}}" in result

    def test_is_idempotent(self, updater: OtherVersionsUpdater) -> None:
        once = updater.ensure_named_param(make_info("{{Svg lang|ar}}"), "Svg lang", "dl", "en")
        assert updater.ensure_named_param(once, "Svg lang", "dl", "en") == once


# -------------------------------------------------------------------- #
# remove_named_param
# -------------------------------------------------------------------- #


class TestRemoveNamedParam:
    def test_removes_param(self, updater: OtherVersionsUpdater) -> None:
        result = updater.remove_named_param(make_info("{{Svg lang|dl=en|ar}}"), "Svg lang", "dl")
        assert "{{Svg lang|ar}}" in result
        assert "dl=" not in result

    def test_removes_every_occurrence(self, updater: OtherVersionsUpdater) -> None:
        result = updater.remove_named_param(make_info("{{Svg lang|dl=a|ar|dl=b}}"), "Svg lang", "dl")
        assert "{{Svg lang|ar}}" in result

    def test_missing_param_returns_text_unchanged(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar}}")
        assert updater.remove_named_param(text, "Svg lang", "dl") == text

    def test_missing_main_template_returns_text_unchanged(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Svg lang|dl=en|ar}}"
        assert updater.remove_named_param(text, "Svg lang", "dl") == text

    def test_other_params_of_the_main_template_are_untouched(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|dl=en|ar}}")
        result = updater.remove_named_param(text, "Svg lang", "dl")
        assert "|description=x" in result
        assert "|author = Someone" in result


# -------------------------------------------------------------------- #
# Locating the parameter and writing it back (_update)
# -------------------------------------------------------------------- #


class TestParameterLookup:
    def test_param_name_with_underscore_is_found(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Information\n|other_versions = {{Svg lang|ar}}\n}}"
        result = updater.merge_values(text, "Svg lang", ["de"])
        assert "|other_versions = {{Svg lang|ar|de}}" in result

    def test_param_name_case_is_ignored(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Information\n|Other Versions = {{Svg lang|ar}}\n}}"
        result = updater.merge_values(text, "Svg lang", ["de"])
        assert "|Other Versions = {{Svg lang|ar|de}}" in result

    def test_param_name_surrounding_spaces_are_ignored(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Information\n|  other versions  = {{Svg lang|ar}}\n}}"
        result = updater.merge_values(text, "Svg lang", ["de"])
        assert "{{Svg lang|ar|de}}" in result
        assert result.count("other versions") == 1

    def test_first_matching_param_name_in_order_is_used(self) -> None:
        custom = OtherVersionsUpdater(param_names=["versions", "other versions"])
        text = "{{Information\n|other versions = {{Svg lang|ar}}\n}}"
        result = custom.merge_values(text, "Svg lang", ["de"])
        assert "{{Svg lang|ar|de}}" in result
        assert "|versions=" not in result

    def test_first_param_name_is_used_when_creating(self) -> None:
        custom = OtherVersionsUpdater(param_names=["versions", "other versions"])
        result = custom.merge_values("{{Information\n|description=x\n}}", "Svg lang", ["ar"])
        assert "|versions={{Svg lang|ar}}" in result
        assert "other versions" not in result

    def test_main_template_name_is_case_and_underscore_insensitive(self) -> None:
        custom = OtherVersionsUpdater(main_template_name="Art_work")
        result = custom.merge_values("{{art work\n|description=x\n}}", "Svg lang", ["ar"])
        assert "{{Svg lang|ar}}" in result

    def test_first_main_template_is_used_when_there_are_several(self, updater: OtherVersionsUpdater) -> None:
        text = make_info("{{Svg lang|ar}}") + "\n" + make_info("{{Svg lang|fa}}")
        result = updater.merge_values(text, "Svg lang", ["de"])
        assert "{{Svg lang|ar|de}}" in result
        assert "{{Svg lang|fa}}" in result


class TestWhitespaceHandling:
    def test_leading_and_trailing_whitespace_around_the_value_is_preserved(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Information\n|other versions =   {{Svg lang|ar}}  \n|author=x\n}}"
        result = updater.merge_values(text, "Svg lang", ["de"])
        assert "|other versions =   {{Svg lang|ar|de}}  \n|author=x" in result

    def test_empty_param_keeps_the_line_break_before_the_next_param(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Information\n|description=x\n|other versions=\n|author=y\n}}"
        result = updater.merge_values(text, "Svg lang", ["ar"])
        assert "|other versions={{Svg lang|ar}}\n|author=y" in result

    def test_unchanged_value_returns_the_original_text_untouched(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Information\n|other versions  =   {{Svg lang|ar}}   \n}}"
        assert updater.merge_values(text, "Svg lang", ["ar"]) == text

    def test_other_params_are_not_reformatted(self, updater: OtherVersionsUpdater) -> None:
        text = "{{Information\n|description   =  x  \n|other versions = {{Svg lang|ar}}\n|author=y\n}}"
        result = updater.merge_values(text, "Svg lang", ["de"])
        assert "|description   =  x  \n" in result
        assert "|author=y\n}}" in result

    def test_text_before_and_after_the_main_template_is_preserved(self, updater: OtherVersionsUpdater) -> None:
        page = "intro\n" + make_info("{{Svg lang|ar}}") + "\noutro"
        result = updater.merge_values(page, "Svg lang", ["de"])
        assert result.startswith("intro\n{{Information")
        assert result.endswith("}}\noutro")
