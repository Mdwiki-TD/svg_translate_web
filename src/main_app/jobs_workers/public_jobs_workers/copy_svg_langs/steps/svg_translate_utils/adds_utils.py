"""
Step for injecting translations into SVG files.

title_new dict data like:
{
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
        "uk": "Поширеність хвороби Паркінсона, 1990"
      }
    },
    "title_new": {
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
        "uk": "Поширеність хвороби Паркінсона, {year}"
      }
    }
  }
"""

from __future__ import annotations

import logging
from typing import Any

from ..mapping import ExtractorData
from .year_handler import YearTitleHandler

logger = logging.getLogger(__name__)


class ByLanguage:

    def __init__(self, lang: str, text: str) -> None:
        self.lang = lang
        self.text = text
        self.ends_data = [
            ", {year}",
            ",{year}",
            "، {year}",
            "،{year}",
        ]

    def abr(self) -> str | None:
        # "abr"	Parkinson yareɛ a ebu soɔ, afe {year}
        if self.text.endswith(", afe {year}"):
            return self.text.removesuffix(", afe {year}").strip()
        else:
            return None

    def ja(self) -> str | None:
        # "ja": {year}年のパーキンソン病の流行
        if self.text.startswith("{year}年の"):
            return self.text.removeprefix("{year}年の").strip()
        elif self.text.startswith("{year}年"):
            return self.text.removeprefix("{year}年").strip()
        elif self.text.endswith("年{year}"):
            return self.text.removesuffix("年{year}").strip()
        else:
            return None

    def multi_langs(self) -> str | None:
        # other languages
        for end_data in self.ends_data:
            if self.text.endswith(end_data):
                return self.text.removesuffix(end_data).strip()
        return None

    def run(self) -> str | None:
        if not self.text:
            return None

        if "{year}" not in self.text:
            return None

        langs_funcs = {
            "abr": self.abr,
            "ja": self.ja,
        }
        if self.lang in langs_funcs:
            return langs_funcs[self.lang]()

        return self.multi_langs()


class TitlesTranslationsRenderer:
    """
    Builds a translations dict from `title_new`-shaped input by stripping
    the trailing/leading `{year}` pattern from both the English key and
    each language's translated text.
    """

    def __init__(self, title_new: dict[str, dict[str, str]]) -> None:
        self.title_new = title_new

    @staticmethod
    def _text_by_lang(lang: str, text: str) -> str | None:
        return ByLanguage(lang, text).run()

    def _render_translations(self, translations: dict[str, str]) -> dict[str, str]:
        new_key_data = {}
        for lang, str_text in translations.items():
            if not str_text:
                continue

            new_text = self._text_by_lang(lang, str_text)
            if new_text and new_text != str_text:
                new_key_data[lang] = new_text

        return new_key_data

    def run(self) -> dict[str, dict[str, str]]:
        data: dict[str, dict[str, str]] = {}

        for en_key, translations in self.title_new.items():
            new_key = self._text_by_lang("en", en_key)
            if new_key is None or new_key == en_key:
                continue

            new_key_data = self._render_translations(translations)
            if new_key_data:
                data[new_key] = new_key_data

        return data


class AddTitlesTranslationsFromTitles:

    def __init__(self, translations: ExtractorData) -> None:
        self.translations = translations
        self.changes: bool | None = None

    def _add_from_titles(self, titles_new: dict[str, dict[str, str]], new_keys: list[str]) -> dict[str, dict[str, str]]:
        title_new_translations = TitlesTranslationsRenderer(titles_new).run()
        result = {x: v for x, v in title_new_translations.items() if x not in new_keys}

        return result

    def run(self) -> ExtractorData:
        """Insert new translations into the translations dictionary."""

        titles_new = self.translations.title_new
        new_translations = self.translations.new

        if not titles_new:
            self.changes = False
            return

        new_keys = list(new_translations.keys())

        new_data = self._add_from_titles(titles_new, new_keys)
        if new_data:
            new_translations.update(new_data)
            self.changes = True
        else:
            self.changes = False


def add_translations_from_titles(translations: dict[str, Any] | ExtractorData) -> dict[str, Any]:
    """Insert new translations into the translations dictionary."""
    object = ExtractorData.from_any(translations)

    bot = AddTitlesTranslationsFromTitles(object)

    bot.run()
    if bot.changes is False:
        return translations

    # if isinstance(translations, ExtractorData): return bot.translations

    data = bot.translations.to_json()

    return data


def add_translations_from_header(translations: dict[str, Any] | ExtractorData) -> dict[str, Any]:
    """Insert new translations into the translations dictionary."""
    object = ExtractorData.from_any(translations)
    header_data = object.meta.get("header", {})

    if not header_data:
        return translations

    new_object = ExtractorData.from_any({"new": header_data})

    bot = YearTitleHandler()
    bot.build_templates(new_object)

    titles_new = new_object.title_new

    if not titles_new:
        return translations

    bot = AddTitlesTranslationsFromTitles(new_object)

    new_data = bot._add_from_titles(titles_new, [])

    if not new_data:
        return translations

    object.new.update(new_data)

    return object.to_json()


__all__ = [
    "add_translations_from_titles",
    "add_translations_from_header",
]
