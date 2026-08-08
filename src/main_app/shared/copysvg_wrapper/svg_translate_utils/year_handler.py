# titles/year_handler.py
from __future__ import annotations

import logging
import re
from typing import Any

from ..mapping import ExtractorData

logger = logging.getLogger(__name__)

YEAR_RE = re.compile(r"\d{4}")


class YearTitleHandler:
    """
    Unified handler for titles that contain a 4-digit year.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------
    @staticmethod
    def match_year(text: str) -> str:
        """
        Return the 4-digit year if it appears at the start or end of the
        string (after stripping), otherwise empty string.
        """
        text = text.strip()
        if len(text) < 4:
            return ""
        if text[-4:].isdigit():
            return text[-4:]
        if text[:4].isdigit():
            return text[:4]
        return ""

    def bulid_lang_template(self, value: str, lang: str) -> str:
        """
        "dag": "Parkinson's doro yɔlibu biɛɣigu ni, yuuni 1990 puli ni",
        "ca": "Prevalència de la malaltia de Parkinson",
        """
        if re.sub(r"\d{4}", "", value) == value:
            return f"{value}, {{year}}"

        if lang == "dag" and "," in value:
            value = value.split(",", maxsplit=1)[0]
            return self.bulid_lang_template(value, "")

        return ""

    @staticmethod
    def replace_year_with_placeholder(text: str, year: str) -> str:
        """
        Replace the year at the start or end with '{year}'.
        Returns empty string if the year is not in the expected position.
        """
        text = text.strip()

        if text.endswith(year):
            return re.sub(r"\d{4}$", "{year}", text)

        if text.startswith(year):
            return re.sub(r"^\d{4}", "{year}", text)

        return ""

    # ------------------------------------------------------------------
    # Extraction side
    # ------------------------------------------------------------------

    def build_templates(self, mapping: ExtractorData) -> None:
        """
        Populate mapping.title_new from mapping.new.

        Example
            -------
            Input (mapping.new):
            "COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020", ...}

            Output (mapping.title_new):
            "COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}", ...}
        """
        data = self.build_title_new_templates(mapping.new)
        if data:
            mapping.title_new.update(data)

    def build_title_new_templates(
        self, mapping_new: dict[str, Any], create_lang_template: bool = False
    ) -> dict[str, Any]:
        """
        Extract valid title translations by verifying that all translations in a mapping
        end with the same 4-digit year as the key.

        Example:
            Input:
                {
                    "COVID-19 pandemic 2020": {"ar": "جائحة كوفيد 2020", "es": "Pandemia de COVID-19 2020"}
                }
            Output:
                {
                    "COVID-19 pandemic {year}": {"ar": "جائحة كوفيد {year}", "es": "Pandemia de COVID-19 {year}"}
                }

        Args:
            new: A dictionary mapping full titles (ending with a year) to their translations.

        Returns:
            A dictionary mapping base title -> { language -> title with `{year}` }.
        """
        data = {}
        for source, translations in list(mapping_new.items()):
            year = self.match_year(source)

            # if not year:
            if not source or source == year or not year.isdigit():
                continue

            source_template = self.replace_year_with_placeholder(source, year)
            if not source_template:
                continue

            templated: dict[str, str] = {}
            for lang, value in translations.items():
                value_template = self.replace_year_with_placeholder(value, year)
                if create_lang_template and not value_template:
                    value_template = self.bulid_lang_template(value, lang)

                if value_template:
                    templated[lang] = value_template

            if templated:
                data[source_template] = templated
                logger.debug("Title template: %r → %s", source_template, list(templated))
        return data


__all__ = [
    "YearTitleHandler",
]
