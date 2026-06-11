import re


def extract_slug(chart_url: str | None) -> str | None:
    """
    Extracts the chart slug from a given Our World in Data URL.

    This function looks specifically for standard grapher URLs and extracts the unique identifier (slug) of the chart,
    ignoring query parameters. If the URL is not a standard grapher link (e.g., explorer links) or is invalid,
    it returns None.

    Args:
        chart_url (str | None): The full URL string of the chart.

    Returns:
        str | None: The extracted slug string if found, otherwise None.

    Examples:
        >>> extract_slug("https://ourworldindata.org/grapher/death-rate-by-source-from-indoor-air-pollution?tab=map")
        'death-rate-by-source-from-indoor-air-pollution'

        >>> extract_slug("https://ourworldindata.org/explorers/democracy?v=1&csvType=full")
        None
    """
    if not chart_url:
        return None

    # Remove query parameters from the URL
    chart_url = chart_url.split("?")[0]

    slug = None
    # Check if it's a valid grapher URL and extract the slug
    if "/grapher/" in chart_url:
        slug = chart_url.split("/grapher/", maxsplit=1)[1]

    return slug


def match_last_world_year(newest_world_file: str) -> int | None:
    """
    Extracts the year from a specific "World" SVG chart filename.

    This function parses filenames from Our World in Data exports to extract the 4-digit year,
    handling both regular and cropped variations.

    Args:
        newest_world_file (str): The filename or path of the SVG file.

    Returns:
        int | None: The extracted 4-digit year as an integer if a match is found, otherwise None.

    Examples:
        >>> match_last_world_year("death-rate-by-source-from-indoor-air-pollution,World,2021.svg")
        2021

        >>> match_last_world_year("death-rate-by-source-from-indoor-air-pollution,World,2021 (cropped).svg")
        2021
    """
    # Extract the 4-digit year before the extension, optionally handling '(cropped)'
    # re.search ensures it finds the pattern even if full paths are passed.
    y_match = re.match(r"^.*?,\s*(\d{4})(\s*\(cropped\))?\.svg$", newest_world_file)
    if y_match:
        return int(y_match.group(1))

    return None


__all__ = [
    "extract_slug",
    "match_last_world_year",
]
