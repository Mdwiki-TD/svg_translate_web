import pytest

from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.mapping import ExtractorData
from src.main_app.jobs_workers.public_jobs_workers.copy_svg_langs.steps.svg_translate_utils import (
    AddTitlesTranslationsFromTitles,
    ByLanguage,
    TitlesTranslationsRenderer,
    add_translations_from_header,
    add_translations_from_titles,
)


def render_translations_for_titles(title_new: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    return TitlesTranslationsRenderer(title_new).run()


# ---------------------------------------------------------------------------
# ByLanguage
# ---------------------------------------------------------------------------


class TestByLanguage:
    def test_run_returns_none_for_empty_text(self):
        # Empty string should short-circuit before any lang-specific logic.
        assert ByLanguage("en", "").run() is None

    def test_run_returns_none_when_no_year_placeholder(self):
        # Text without "{year}" is not a candidate for translation stripping.
        assert ByLanguage("en", "parkinson's disease prevalence").run() is None

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("parkinson's disease prevalence, {year}", "parkinson's disease prevalence"),
            ("parkinson's disease prevalence,{year}", "parkinson's disease prevalence"),
        ],
    )
    def test_multi_langs_comma_suffix(self, text, expected):
        # Generic comma + "{year}" suffix stripping (used for "en", "es", etc.).
        assert ByLanguage("en", text).run() == expected

    def test_multi_langs_arabic_comma_suffix(self):
        # Arabic comma variant "، {year}".
        text = "انتشار مرض باركنسون، {year}"
        expected = "انتشار مرض باركنسون"
        assert ByLanguage("ar", text).run() == expected

    def test_multi_langs_arabic_comma_no_space_suffix(self):
        # Arabic comma variant without a following space "،{year}".
        text = "انتشار مرض باركنسون،{year}"
        expected = "انتشار مرض باركنسون"
        assert ByLanguage("ar", text).run() == expected

    def test_multi_langs_returns_none_when_no_known_suffix(self):
        # "{year}" is present but not in any recognized suffix pattern.
        assert ByLanguage("es", "algo {year} raro").run() is None

    def test_abr_strips_known_suffix(self):
        text = "Parkinson yareɛ a ebu soɔ, afe {year}"
        expected = "Parkinson yareɛ a ebu soɔ"
        assert ByLanguage("abr", text).run() == expected

    def test_abr_returns_none_when_suffix_does_not_match(self):
        # "abr" only recognizes ", afe {year}", not the generic comma suffix.
        text = "Parkinson yareɛ a ebu soɔ, {year}"
        assert ByLanguage("abr", text).run() is None

    def test_ja_strips_prefix(self):
        text = "{year}年のパーキンソン病の流行"
        # expected = "のパーキンソン病の流行"
        expected = "パーキンソン病の流行"
        assert ByLanguage("ja", text).run() == expected

    def test_ja_strips_suffix(self):
        text = "パーキンソン病の流行年{year}"
        expected = "パーキンソン病の流行"
        assert ByLanguage("ja", text).run() == expected

    def test_ja_returns_none_when_no_known_pattern(self):
        text = "パーキンソン病の流行 {year}"
        assert ByLanguage("ja", text).run() is None


# ---------------------------------------------------------------------------
# TitlesTranslationsRenderer
# ---------------------------------------------------------------------------


class TestRenderTitlesTranslations:
    def test_full_example_from_docstring(self):
        title_new = {
            "parkinson's disease prevalence, {year}": {
                "abr": "Parkinson yareɛ a ebu soɔ, afe {year}",
                "ar": "انتشار مرض باركنسون، {year}",
                "cs": "Prevalence Parkinsonovy nemoci, {year}",
                "es": "Prevalencia de la enfermedad de Parkinson, {year}",
                "eu": "Parkinsonen gaixotasunaren prebalentzia, {year}",
                "gpe": "Parkinson ein disease prevalence, {year}",
                "id": "Prevalensi penyakit Parkinson, {year}",
                "ja": "{year}年のパーキンソン病の流行",
                "pt": "Prevalência de doença de Parkinson, {year}",
                "si": "පාකින්සන් රෝග ව්‍යාප්තිය, {year}",
                "uk": "Поширеність хвороби Паркінсона, {year}",
            }
        }

        result = render_translations_for_titles(title_new)

        expected_key = "parkinson's disease prevalence"
        assert expected_key in result
        assert result[expected_key]["ar"] == "انتشار مرض باركنسون"
        # assert result[expected_key]["ja"] == "のパーキンソン病の流行"
        assert result[expected_key]["ja"] == "パーキンソン病の流行"
        # "abr" recognizes its own specific suffix.
        assert result[expected_key]["abr"] == "Parkinson yareɛ a ebu soɔ"
        assert result[expected_key]["es"] == "Prevalencia de la enfermedad de Parkinson"
        # Exactly the 11 languages provided should be present.
        assert len(result[expected_key]) == 11

    def test_skips_english_key_without_year_placeholder(self):
        # This is the bug fix: keys with no "{year}" must not leak into
        # the result as a `None` key.
        title_new = {
            "a title with no year placeholder": {
                "es": "un titulo sin marcador de año",
            }
        }
        result = render_translations_for_titles(title_new)
        assert result == {}
        assert None not in result

    def test_skips_key_when_stripping_does_not_change_it(self):
        # If removing the suffix pattern produces the exact same string
        # (i.e. there was nothing to strip / no matching suffix), skip it.
        title_new = {
            "some title {year} in the middle": {
                "es": "algun titulo {year} en el medio",
            }
        }
        result = render_translations_for_titles(title_new)
        assert result == {}

    def test_skips_translation_when_stripped_text_unchanged(self):
        # Per-language translations that don't actually change after
        # stripping should not be included, even if the English key does.
        title_new = {
            "prevalence, {year}": {
                "es": "prevalencia {year}",  # no matching suffix pattern -> None -> skipped
                "ar": "الانتشار، {year}",
            }
        }
        result = render_translations_for_titles(title_new)
        assert "prevalence" in result
        assert "es" not in result["prevalence"]
        assert result["prevalence"]["ar"] == "الانتشار"

    def test_skips_empty_translation_values(self):
        # Empty strings must be ignored, not passed to ByLanguage.
        title_new = {
            "prevalence, {year}": {
                "es": "",
                "ar": "الانتشار، {year}",
            }
        }
        result = render_translations_for_titles(title_new)
        assert "es" not in result["prevalence"]
        assert result["prevalence"]["ar"] == "الانتشار"

    def test_key_dropped_when_all_translations_are_empty_result(self):
        # If, after filtering, no translations survive for a key, that
        # key should not appear in the final output at all.
        title_new = {
            "prevalence, {year}": {
                "es": "prevalencia {year}",  # unmatched suffix -> None
            }
        }
        result = render_translations_for_titles(title_new)
        assert result == {}

    def test_empty_input_returns_empty_dict(self):
        assert render_translations_for_titles({}) == {}


# ---------------------------------------------------------------------------
# add_translations_from_titles
# ---------------------------------------------------------------------------


class TestAddTranslationsFromTitles:
    def test_returns_unchanged_when_title_new_missing(self):
        translations = {"new": {"existing key": {"es": "existente"}}}
        result = add_translations_from_titles(translations)
        assert result == translations

    def test_merges_new_key_into_new_dict(self):
        translations = {
            "new": {"other title": {"es": "otro titulo"}},
            "title_new": {
                "prevalence, {year}": {"ar": "الانتشار، {year}"},
            },
        }
        expectrd_translations = {
            "new": {
                "other title": {"es": "otro titulo"},
                "prevalence": {"ar": "الانتشار"},
            },
            "title_new": {
                "prevalence, {year}": {"ar": "الانتشار، {year}"},
            },
        }
        result = add_translations_from_titles(translations)
        assert "prevalence" in result["new"]
        assert result["new"]["prevalence"]["ar"] == "الانتشار"
        assert result["new"] == expectrd_translations["new"]
        assert result["title_new"] == expectrd_translations["title_new"]
        assert result["error"] == ""
        assert result["meta"] == {}

    def test_merge_when_new_dict_is_empty(self):
        translations = {
            "new": {},
            "title_new": {
                "prevalence, {year}": {"ar": "الانتشار، {year}"},
            },
        }
        result = add_translations_from_titles(translations)
        assert result["new"] == {"prevalence": {"ar": "الانتشار"}}

    def test_merge_with_undifined_keys(self):
        translations = {
            "zz": {},
            "title_new": {
                "prevalence, {year}": {"ar": "الانتشار، {year}"},
            },
        }
        result = add_translations_from_titles(translations)
        assert result["new"] == {"prevalence": {"ar": "الانتشار"}}

    def test_does_not_overwrite_existing_key_in_new(self):
        # Keys already present in "new" must be excluded from the merge,
        # even if title_new would have produced the same key.
        translations = {
            "new": {
                "prevalence": {"ar": "قيمة قديمة"},
            },
            "title_new": {
                "prevalence, {year}": {"ar": "الانتشار، {year}"},
            },
        }
        result = add_translations_from_titles(translations)
        assert result["new"]["prevalence"]["ar"] == "قيمة قديمة"
        assert result == translations

    def test_no_update_when_title_new_produces_nothing(self):
        # If title_new yields no valid translations, "new" stays untouched.
        translations = {
            "new": {"other": {"es": "otro"}},
            "title_new": {
                "no year placeholder here": {"es": "algo"},
            },
        }
        original_new = dict(translations["new"])
        result = add_translations_from_titles(translations)
        assert result["new"] == original_new

    def test_returns_same_dict_object(self):
        # The function mutates and returns the same translations dict. when no title_new found
        translations = {
            "new": {},
            "title_newz": {
                "prevalence, {year}": {"ar": "الانتشار، {year}"},
            },
        }
        result = add_translations_from_titles(translations)
        assert result is translations


class TestAddTranslationsWithExtractorData:

    def test_adds_translations(self):
        data = {
            "new": {
                "test": {
                    "ar": "تجربة",
                },
            },
            "title_new": {
                "prevalence, {year}": {
                    "ar": "الانتشار، {year}",
                },
            },
        }
        translations = ExtractorData.from_any(data)

        result = add_translations_from_titles(translations)
        assert result["new"]["prevalence"]["ar"] == "الانتشار"
        # assert result == translations

    def test_return_same_object(self):
        data = {
            "new": {},
            "random": {
                "prevalence, {year}": {
                    "ar": "الانتشار، {year}",
                },
            },
        }
        translations = ExtractorData.from_any(data)

        result = add_translations_from_titles(translations)
        assert result is translations

    def test_new_obj(self):
        data = {
            "new": {
                "parkinson's disease prevalence, 1990": {
                    "ja": "1990年のパーキンソン病の流行",
                    "abr": "Parkinson yareɛ a ebu soɔ, afe 1990",
                    "ar": "انتشار مرض باركنسون، 1990",
                    "ca": "Prevalència de la malaltia de Parkinson",
                },
            },
            "title_new": {
                "prevalence, {year}": {
                    "ar": "الانتشار، {year}",
                },
            },
        }
        translations = ExtractorData.from_any(data)

        bot = AddTitlesTranslationsFromTitles(translations)

        bot.run()

        result = bot.translations

        assert isinstance(result, ExtractorData)

        assert result == translations
        assert result.to_json() == {
            "new": {
                "parkinson's disease prevalence, 1990": {
                    "ja": "1990年のパーキンソン病の流行",
                    "abr": "Parkinson yareɛ a ebu soɔ, afe 1990",
                    "ar": "انتشار مرض باركنسون، 1990",
                    "ca": "Prevalència de la malaltia de Parkinson",
                },
                "prevalence": {"ar": "الانتشار"},
            },
            "tspans_by_id": {},
            "title_new": {"prevalence, {year}": {"ar": "الانتشار، {year}"}},
            "meta": {},
            "error": "",
        }


class TestWithMeta:

    def test_new_obj(self):
        data = {
            "new": {},
            "meta": {
                "header": {
                    "parkinson's disease prevalence, 1990": {
                        "abr": "Parkinson yareɛ a ebu soɔ, afe 1990",
                        "ar": "انتشار مرض باركنسون، 1990",
                        "ca": "Prevalència de la malaltia de Parkinson",
                        "cs": "Prevalence Parkinsonovy nemoci, 1990",
                        "es": "Prevalencia de la enfermedad de Parkinson, 1990",
                        "eu": "Parkinsonen gaixotasunaren prebalentzia, 1990",
                        "gpe": "Parkinson ein disease prevalence, 1990",
                        "id": "Prevalensi penyakit Parkinson, 1990",
                        "ja": "1990年のパーキンソン病の流行",
                        "pt": "Prevalência de doença de Parkinson, 1990",
                        "si": "පාකින්සන් රෝග ව්‍යාප්තිය, 1990",
                        "uk": "Поширеність хвороби Паркінсона, 1990",
                    }
                }
            },
            "title_new": {},
        }
        translations = ExtractorData.from_any(data)

        bot = AddTitlesTranslationsFromTitles(translations)

        bot.run()

        result = bot.translations
        assert isinstance(result, ExtractorData)
        assert result.new == data["new"]

        # assert json.dumps(result.to_json(), ensure_ascii=False) == "{}"


class TestFromHeader:

    def test_new_obj_with_header(self):
        data = {
            "new": {},
            "meta": {
                "header": {
                    "parkinson's disease prevalence, 1990": {
                        "dag": "Parkinson's doro yɔlibu biɛɣigu ni, yuuni 1990 puli ni",
                        "abr": "Parkinson yareɛ a ebu soɔ, afe 1990",
                        "ar": "انتشار مرض باركنسون، 1990",
                        "ca": "Prevalència de la malaltia de Parkinson",
                        "cs": "Prevalence Parkinsonovy nemoci, 1990",
                        "es": "Prevalencia de la enfermedad de Parkinson, 1990",
                        "eu": "Parkinsonen gaixotasunaren prebalentzia, 1990",
                        "gpe": "Parkinson ein disease prevalence, 1990",
                        "id": "Prevalensi penyakit Parkinson, 1990",
                        "ja": "1990年のパーキンソン病の流行",
                        "pt": "Prevalência de doença de Parkinson, 1990",
                        "si": "පාකින්සන් රෝග ව්‍යාප්තිය, 1990",
                        "uk": "Поширеність хвороби Паркінсона, 1990",
                    }
                },
            },
            "title_new": {},
        }
        result = add_translations_from_header(data)

        assert result["new"] == {
            "parkinson's disease prevalence": {
                "abr": "Parkinson yareɛ a ebu soɔ",
                "ar": "انتشار مرض باركنسون",
                "ca": "Prevalència de la malaltia de Parkinson",
                "dag": "Parkinson's doro yɔlibu biɛɣigu ni",
                "cs": "Prevalence Parkinsonovy nemoci",
                "es": "Prevalencia de la enfermedad de Parkinson",
                "eu": "Parkinsonen gaixotasunaren prebalentzia",
                "gpe": "Parkinson ein disease prevalence",
                "id": "Prevalensi penyakit Parkinson",
                "ja": "パーキンソン病の流行",
                "pt": "Prevalência de doença de Parkinson",
                "si": "පාකින්සන් රෝග ව්‍යාප්තිය",
                "uk": "Поширеність хвороби Паркінсона",
            }
        }
        header_lang_keys = list(data["meta"]["header"]["parkinson's disease prevalence, 1990"].keys())
        result_lang_keys = list(result["new"]["parkinson's disease prevalence"].keys())

        assert header_lang_keys == result_lang_keys

        assert len(header_lang_keys) == len(result_lang_keys)

        # assert json.dumps(result, ensure_ascii=False) == "{}"
