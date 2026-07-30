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
        if "{year}" not in self.text:
            return None

        langs_funcs = {
            "abr": self.abr,
            "ja": self.ja,
        }
        if self.lang in langs_funcs:
            return langs_funcs[self.lang]()

        return self.multi_langs()


def text_by_lang(lang: str, text: str) -> str | None:
    return ByLanguage(lang, text).run()


def render_titles_translations(title_new: dict[str, dict[str, str]]) -> dict[str, dict[str, Any]]:
    """ """
    data = {}

    for en_key, translations in title_new.items():
        new_key = text_by_lang("en", en_key)
        if new_key == en_key:
            continue

        new_key_data = {}
        for lang, str_text in translations.items():
            if not str_text:
                continue

            new_text = text_by_lang(lang, str_text)
            if new_text and new_text != str_text:
                new_key_data[lang] = new_text

        if new_key_data:
            data[new_key] = new_key_data

    return data


__all__ = [
    "render_titles_translations",
]
