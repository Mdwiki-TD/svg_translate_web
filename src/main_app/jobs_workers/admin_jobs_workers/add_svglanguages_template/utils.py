import re

RE_SVG_LANG = re.compile(r"\{\{\s*SVGLanguages\s*\|\s*([^}|]+)", re.I)
# *'''Translate''': https://svgtranslate.toolforge.org/File:share_with_mental_and_substance_disorders,_World,_1990.svg
RE_TRANSLATE = re.compile(
    r"\*\s*'''Translat\w+'''\s*:\s*https://svgtranslate\.toolforge\.org/File:([^ \n]+)",
    re.I,
)


def extract_svg_file_name(text: str) -> str | None:
    """Extract SVG file name from the Translate link in page wikitext.

    Args:
        text: Full wikitext of an OWID page.

    Returns:
        The SVG file name (without ``File:`` prefix), or ``None`` if not found.
    """
    match = RE_TRANSLATE.search(text)
    if match:
        return match.group(1).strip()
    return None


def add_template_to_text(text: str, template_text) -> str:
    if not RE_TRANSLATE.search(text):
        return text

    return re.sub(RE_TRANSLATE, lambda m: m.group(0) + "\n*" + template_text, text, count=1)


__all__ = [
    "RE_SVG_LANG",
    "RE_TRANSLATE",
    "extract_svg_file_name",
    "add_template_to_text",
]
