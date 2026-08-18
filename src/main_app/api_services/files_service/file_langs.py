from __future__ import annotations

import logging

import requests

from .files_helpers import get_file_info
from .objects import FileLanguagesMap

logger = logging.getLogger(__name__)


def get_file_languages(
    file_name: str,
    session: requests.Session | None = None,
) -> FileLanguagesMap:
    """
    Extract available SVG translation languages for a given Commons file.

    Args:
        file_name: Name of the file on Wikimedia Commons.
        session: Optional pre-configured requests session.

    Returns:
        A `FileLanguagesMap` instance with `error` (if any) and `langs` list.
    To mirror:
        https://svgtranslate.toolforge.org/api/languages/File:Parkinsons_disease_prevalence_ihme,_Africa,_2021.svg
    """
    if not file_name:
        return FileLanguagesMap(error="Empty fileName")

    # Normalize file name by stripping leading "File:" prefix
    file_name = file_name.strip()
    normalized_name = file_name[5:] if file_name.lower().startswith("file:") else file_name
    prefixed_file_name = f"File:{normalized_name}"

    file_info = get_file_info(prefixed_file_name, session=session)
    # check if image exists
    if file_info.exists is False:
        return FileLanguagesMap(error="File does not exist")

    # Extract metadata array
    imageinfo = file_info.imageinfo
    if not imageinfo:
        return FileLanguagesMap(
            error=f"Metadata not found for {prefixed_file_name}. Error: {file_info.error}",
        )

    # metadata shema: [ { "name": "version", "value": 2 }, ... , { "name": "translations", "value": []} ]
    metadata = imageinfo[0].get("metadata", [])
    if not metadata:
        return FileLanguagesMap(error=f"Metadata array empty for {prefixed_file_name}")

    translations: list[object] = []
    for entry in metadata:
        if isinstance(entry, dict) and entry.get("name") == "translations":
            value = entry.get("value")
            translations = value if isinstance(value, list) else []
            break

    # translations shema: [ { "name": "abr", "value": 2 }, { "name": "ar", "value": 2 }, ... ]
    if isinstance(translations, list) and len(translations) > 0:
        # Extract language codes from translation entries
        langs_keys = [t["name"] for t in translations if isinstance(t, dict) and "name" in t]
        langs_keys.append("en")
        return FileLanguagesMap(langs=langs_keys)

    return FileLanguagesMap(langs=["en"])


__all__ = [
    "FileLanguagesMap",
    "get_file_languages",
]
