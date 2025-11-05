#
import logging
from ...web.commons import get_wikitext

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
