#
import logging
from ..web.commons import get_files, get_wikitext

logger = logging.getLogger("svg_translate")


def text_task(stages, title):
    """Fetch wikitext for a Commons file and update stage metadata.

    Parameters:
        stages (dict): Mutable stage metadata for the text stage.
        title (str): Commons title whose wikitext should be retrieved.

    Returns:
        tuple: ``(text, stages)`` where ``text`` is the retrieved wikitext (empty
        string on failure) and ``stages`` reflects the final status update.
    """

    stages["status"] = "Running"

    stages["sub_name"] = title  # commons_link(title)
    stages["message"] = "Load wikitext"
    # ---
    text = get_wikitext(title)

    if not text:
        stages["status"] = "Failed"
        logger.error("NO TEXT")
    else:
        stages["status"] = "Completed"
    return text, stages


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
