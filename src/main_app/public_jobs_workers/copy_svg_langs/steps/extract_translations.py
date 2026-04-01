"""Step for extracting translations from a main SVG file."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from CopySVGTranslation import extract  # type: ignore

from ....api_services.utils import download_one_file

logger = logging.getLogger(__name__)


def extract_translations_step(main_title: str, output_dir_main: Path) -> dict[str, Any]:
    """
    Load SVG translations from a Wikimedia Commons main file.

    Args:
        main_title: Commons file title (e.g., "Example.svg") to download and extract translations from.
        output_dir_main: Directory where the downloaded main file is placed.

    Returns:
        dict with keys: success (bool), translations (dict), error (str|None)
    """
    logger.info(f"Extracting translations from main file: {main_title}")

    files1 = download_one_file(title=main_title, out_dir=output_dir_main, i=0, overwrite=True)

    if not files1.get("path"):
        error = f"Error when downloading main file: {main_title}"
        logger.error(error)
        return {"success": False, "translations": {}, "error": error}

    main_title_path = files1["path"]
    translations = extract(main_title_path, case_insensitive=True)

    new_translations = (translations.get("new") or {}) if isinstance(translations, dict) else {}
    new_translations_count = len(new_translations)

    if new_translations_count == 0:
        error = f"No translations found in main file: {main_title}"
        logger.debug(error)
        return {"success": False, "translations": {}, "error": error}

    return {"success": True, "translations": translations, "error": None}
