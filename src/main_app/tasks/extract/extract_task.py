#
import logging

from CopySVGTranslation import extract  # type: ignore

from ..downloads.download_file_utils import download_one_file
from ..tasks_utils import json_save

logger = logging.getLogger(__name__)


def translations_task(stages, main_title, output_dir_main):
    """
    Load SVG translations from a Wikimedia Commons main file, save them as translations.json next to the provided output path, and update the given stages status mapping.

    Parameters:
        stages (dict): Mutable mapping updated with progress keys such as "sub_name", "message", and "status".
        main_title (str): Commons file title (e.g., "Example.svg") to download and extract translations from.
        output_dir_main (pathlib.Path): Directory where the downloaded main file is placed; the function writes translations.json to output_dir_main.parent.

    Returns:
        tuple: (translations, stages) where `translations` is a dict of extracted translations (empty if none were found or download failed) and `stages` is the same stages mapping updated to reflect the final status and messages.
    """
    stages["sub_name"] = f"File:{main_title}"  # commons_link(f'File:{main_title}')
    # ---
    stages["message"] = "Load translations from main file"
    # ---
    stages["status"] = "Running"
    # ---
    files1 = download_one_file(title=main_title, out_dir=output_dir_main, i=0, overwrite=True)
    # ---
    if not files1.get("path"):
        logger.error(f"when downloading main file: {main_title}")
        stages["message"] = "Error when downloading main file"
        stages["status"] = "Failed"
        return {}, stages

    main_title_path = files1["path"]
    translations = extract(main_title_path, case_insensitive=True)

    new_translations = (translations.get("new") or {}) if isinstance(translations, dict) else {}
    new_translations_count = len(new_translations)

    if new_translations_count == 0:
        logger.debug(f"No translations found in main file: {main_title}")
        stages["status"] = "Failed"
        stages["message"] = "No translations found in main file"
        return {}, stages

    stages["status"] = "Completed"
    stages["message"] = f"Loaded {new_translations_count:,} translations from main file"

    json_save(output_dir_main.parent / "translations.json", translations)

    return translations, stages
