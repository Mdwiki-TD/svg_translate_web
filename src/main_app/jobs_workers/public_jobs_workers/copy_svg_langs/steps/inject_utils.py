"""
Step for injecting translations into SVG files.

title_new dict data like:
{
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
        if self.text.startswith("{year}年"):
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


def text_by_lang(lang: str, text: str) -> str | None:
    return ByLanguage(lang, text).run()


def render_titles_translations(title_new: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    return TitlesTranslationsRenderer(title_new).run()


def _add_from_titles(titles_new: dict[str, dict[str, str]], new_keys: list[str]) -> dict[str, dict[str, str]]:
    title_new_translations = render_titles_translations(titles_new)
    result = {}

    for x, data in title_new_translations.items():
        if x not in new_keys:
            result[x] = data

    return result


def add_translations_from_titles(translations: dict[str, Any]) -> dict[str, Any]:
    """Insert new translations into the translations dictionary."""

    title_new = translations.get("title_new")
    new_translations = translations.get("new")

    if title_new is None or new_translations is None:
        return translations

    new_keys = list(translations["new"].keys())
    add_translations = _add_from_titles(translations["title_new"], new_keys)
    if add_translations:
        translations["new"].update(add_translations)

    return translations


__all__ = [
    "add_translations_from_titles",
]
