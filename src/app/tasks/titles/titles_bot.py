#
import logging
from ...commons import get_files

logger = logging.getLogger("svg_translate")


def titles_task(stages, text, manual_main_title, titles_limit=None):
    """Extract SVG titles from wikitext and update stage metadata.

    Parameters:
        stages (dict): Mutable stage metadata for the titles stage.
        text (str): Wikitext retrieved from the main Commons page.
        manual_main_title (str | None): Optional title to use instead of the extracted main_title.
        titles_limit (int | None): Optional maximum number of titles to keep.

    Returns:
        tuple: ``({"main_title": str | None, "titles": list[str]}, stages)`` with
        the updated stage metadata.
    """

    stages["status"] = "Running"

    main_title, titles = get_files(text)

    if manual_main_title:
        main_title = manual_main_title

    if not titles or not main_title:
        stages["status"] = "Failed"
        logger.error("no titles")
    else:
        stages["status"] = "Completed"

    stages["message"] = f"Found {len(titles):,} titles"

    if titles_limit and titles_limit > 0 and len(titles) > titles_limit:
        stages["message"] += f", use only {titles_limit:,}"
        # use only n titles
        titles = titles[:titles_limit]

    if not main_title:
        stages["message"] += ", no main title found"

    data = {
        "main_title": main_title,
        "titles": titles
    }

    return data, stages
