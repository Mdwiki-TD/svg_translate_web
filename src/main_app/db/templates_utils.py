import re


def extract_slug(chart_url: str | None) -> str | None:
    """
    examples:
    input:
        https://ourworldindata.org/grapher/death-rate-by-source-from-indoor-air-pollution?tab=map
    output:
        death-rate-by-source-from-indoor-air-pollution
    ----
    input:
        https://ourworldindata.org/explorers/democracy?v=1&csvType=full&useColumnShortNames=true&Dataset=Regimes+of+the+World&Metric=%C2%ADLiberal+democracy&Sub-metric=Transparent+laws
    output:
        None
    """
    if not chart_url:
        return None

    chart_url = chart_url.split("?")[0]

    slug = None
    if "/grapher/" in chart_url:
        slug = chart_url.split("/grapher/", maxsplit=1)[1]

    return slug


def match_last_world_year(last_world_file) -> int | None:
    """
    input:
        death-rate-by-source-from-indoor-air-pollution,World,2021.svg
        death-rate-by-source-from-indoor-air-pollution,World,2021 (cropped).svg
    output:
        2021
    """
    # match year
    y_match = re.match(r"^.*?,\s*(\d{4})(\s*\(cropped\))?\.svg$", last_world_file)
    if y_match:
        return int(y_match.group(1))

    return None


__all__ = [
    "extract_slug",
    "match_last_world_year",
]
