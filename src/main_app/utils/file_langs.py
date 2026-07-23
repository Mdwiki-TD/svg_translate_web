from __future__ import annotations

import logging
from typing import Any

import requests

from ..api_services import create_commons_session
from ..config import settings

logger = logging.getLogger(__name__)

LANG_CODE_CATEGORY_MAP: dict[str, str] = {
    "ar": "Arabic-language SVG",
    "bar": "Bavarian-language SVG",
    "be": "Belarusian-language SVG",
    "bg": "Bulgarian-language SVG",
    "bh": "Bhojpuri-language SVG",
    "bjn": "Banjar-language SVG",
    "blk": "Pa'O-language SVG",
    "bn": "Bengali-language SVG",
    "bs": "Bosnian-language SVG",
    "ca": "Catalan-language SVG",
    "ckt": "Chukchi-language SVG",
    "cs": "Czech-language SVG",
    "cy": "Welsh-language SVG",
    "da": "Danish-language SVG",
    "de": "German-language SVG",
    "el": "Greek-language SVG",
    "en": "English-language SVG",
    "eo": "Esperanto-language SVG",
    "es": "Spanish-language SVG",
    "et": "Estonian-language SVG",
    "eu": "Basque-language SVG",
    "fa": "Persian-language SVG",
    "fi": "Finnish-language SVG",
    "fr": "French-language SVG",
    "fy": "Frisian-language SVG",
    "ga": "Irish-language SVG",
    "gag": "Gagauz-language SVG",
    "gl": "Galician-language SVG",
    "got": "Gothic-language SVG",
    "gu": "Gujarati-language SVG",
    "he": "Hebrew-language SVG",
    "hi": "Hindi-language SVG",
    "hr": "Croatian-language SVG",
    "hsb": "Sorbian-language SVG",
    "ht": "Haitian Creole-language SVG",
    "hu": "Hungarian-language SVG",
    "ia": "Interlingua-language SVG",
    "id": "Indonesian-language SVG",
    "is": "Icelandic-language SVG",
    "isv": "Interslavic-language SVG",
    "it": "Italian-language SVG",
    "ja": "Japanese-language SVG",
    "jv": "Javanese-language SVG",
    "ka": "Georgian-language SVG",
    "kk": "Kazakh-language SVG",
    "kn": "Kannada-language SVG",
    "ko": "Korean-language SVG",
    "ks": "Kashmiri-language SVG",
    "ksh": "Ripuarian-language SVG",
    "ku": "Kurdish-language SVG",
    "ky": "Kyrgyz-language SVG",
    "la": "Latin-language SVG",
    "lb": "Luxembourgish-language SVG",
    "lrc": "Luri-language SVG",
    "lt": "Lithuanian-language SVG",
    "lv": "Latvian-language SVG",
    "mag": "Magahi-language SVG",
    "mai": "Maithili-language SVG",
    "mdf": "Moksha-language SVG",
    "mg": "Malagasy-language SVG",
    "mi": "Maori-language SVG",
    "mk": "Macedonian-language SVG",
    "ml": "Malayalam-language SVG",
    "mn": "Mongolian-language SVG",
    "mr": "Marathi-language SVG",
    "mrj": "Hill Mari-language SVG",
    "ms": "Malay-language SVG",
    "mt": "Maltese-language SVG",
    "my": "Burmese-language SVG",
    "nds": "Low German-language SVG",
    "ne": "Nepali-language SVG",
    "nl": "Dutch-language SVG",
    "no": "Norwegian-language SVG",
    "nrm": "Norman-language SVG",
    "pa": "Punjabi-language SVG",
    "pl": "Polish-language SVG",
    "pms": "Piedmontese-language SVG",
    "prs": "Dari-language SVG",
    "pt": "Portuguese-language SVG",
    "qu": "Quechua-language SVG",
    "rm": "Romansh-language SVG",
    "ro": "Romanian-language SVG",
    "ru": "Russian-language SVG",
    "rue": "Rusyn-language SVG",
    "sa": "Sanskrit-language SVG",
    "sat": "Santali-language SVG",
    "sco": "Scots-language SVG",
    "sd": "Sindhi-language SVG",
    "se": "Northern Sami-language SVG",
    "sh": "Serbo-Croatian-language SVG",
    "si": "Sinhala-language SVG",
    "sk": "Slovak-language SVG",
    "sl": "Slovene-language SVG",
    "smn": "Inari Sami-language SVG",
    "sms": "Skolt Sami-language SVG",
    "so": "Somali-language SVG",
    "sr": "Serbian-language SVG",
    "sv": "Swedish-language SVG",
    "sw": "Swahili-language SVG",
    "syl": "Sylheti-language SVG",
    "ta": "Tamil-language SVG",
    "te": "Telugu-language SVG",
    "th": "Thai-language SVG",
    "tl": "Tagalog-language SVG",
    "tr": "Turkish-language SVG",
    "tt": "Tatar-language SVG",
    "tup": "Tupi-language SVG",
    "udm": "Udmurt-language SVG",
    "uk": "Ukrainian-language SVG",
    "ur": "Urdu-language SVG",
    "uz": "Uzbek-language SVG",
    "vec": "Venetian-language SVG",
    "vi": "Vietnamese-language SVG",
    "wa": "Walloon-language SVG",
    "yi": "Yiddish-language SVG",
    "yo": "Yoruba-language SVG",
    "zh": "Chinese-language SVG",
    "zu": "Zulu-language SVG",
}


def lang_code_category(langcode: str) -> str | None:
    return LANG_CODE_CATEGORY_MAP.get(langcode)


def get_file_languages(file_name: str, session: requests.Session | None = None) -> dict[str, Any]:
    """
    Extract available SVG translation languages for a given Commons file.

    Args:
        file_name: Name of the file on Wikimedia Commons.
        session: Optional pre-configured requests session.

    Returns:
        Dictionary containing an 'error' message (if any) and a 'langs' list.
    """
    if not file_name:

        return {"error": "Empty fileName", "langs": None}
    if not session:
        session = create_commons_session(settings.other.user_agent)

    # Normalize file name by stripping leading "File:" prefix
    stripped_name = file_name.strip()
    normalized_name = stripped_name[5:] if stripped_name.lower().startswith("file:") else stripped_name

    # Define API endpoint and parameters
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "titles": f"File:{normalized_name}",
        "prop": "imageinfo",
        "iiprop": "metadata",
        "formatversion": "2",
        "format": "json",
    }

    try:
        response = session.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as err:
        logger.exception("Commons API request failed for %s", file_name)
        return {"error": f"API error: {err}", "langs": None}

    pages = data.get("query", {}).get("pages", [])
    if not pages:
        return {"error": "Unexpected API response", "langs": None}

    page = pages[0]

    # Check if file exists
    if page.get("missing") and not page.get("known"):
        return {"error": f"File {page.get('title', normalized_name)} does not exist.", "langs": None}

    # Extract metadata array
    imageinfo = page.get("imageinfo", [])
    if not imageinfo:
        return {"error": f"Metadata not found for {page.get('title')}", "langs": None}

    metadata = imageinfo[0].get("metadata", [])
    if not metadata:
        return {"error": f"Metadata array empty for {page.get('title')}", "langs": None}

    # Convert list of dicts [{'name': ..., 'value': ...}] into a single dictionary
    meta = {
        item["name"]: item["value"]
        for item in metadata
        if isinstance(item, dict) and "name" in item and "value" in item
    }

    translations = meta.get("translations", [])

    if isinstance(translations, list) and len(translations) > 0:
        # Extract language codes from translation entries
        langs_keys = [t["name"] for t in translations if isinstance(t, dict) and "name" in t]
        return {"error": None, "langs": langs_keys if langs_keys else ["en"]}

    return {"error": None, "langs": ["en"]}
